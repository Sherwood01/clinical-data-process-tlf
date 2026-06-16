#!/bin/bash
set -e

# ============= ROTATED SECRETS OVERLAY =============
if [ -f /run/stack-auth/rotated-secrets.env ]; then
  set -a
  source /run/stack-auth/rotated-secrets.env
  set +a
fi

# ============= FORWARD MOCK OAUTH SERVER =============
if [ "$STACK_FORWARD_MOCK_OAUTH_SERVER" = "true" ]; then
  socat TCP-LISTEN:32202,fork,reuseaddr TCP:host.docker.internal:32202 &
fi

# ============= ENV VARS =============
if [ "$NEXT_PUBLIC_STACK_IS_LOCAL_EMULATOR" = "true" ]; then
  for v in STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY; do
    if [ -z "${!v:-}" ]; then
      echo "$v must be set in local-emulator mode (injected by the QEMU VM)." >&2
      exit 1
    fi
  done
  export STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY
else
  export STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY=${STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY:-$(openssl rand -base64 32)}
  export STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY=${STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY:-$(openssl rand -base64 32)}
  export STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY=${STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY:-$(openssl rand -base64 32)}
fi

export NEXT_PUBLIC_STACK_PROJECT_ID=internal
export NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=${STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY}
if [ -n "${STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY:-}" ]; then
  export STACK_SECRET_SERVER_KEY=${STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY}
fi

# Ensure STACK_SERVER_SECRET is set for the API server
export STACK_SERVER_SECRET=${STACK_SERVER_SECRET:-$(openssl rand -base64 32)}
if [ -n "${STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY:-}" ]; then
  export STACK_SUPER_SECRET_ADMIN_KEY=${STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY}
fi

# ============= HEXCLAVE ↔ STACK URL MIRROR =============
for _legacy in STACK_API_URL STACK_DASHBOARD_URL STACK_SVIX_SERVER_URL; do
  _new=HEXCLAVE_${_legacy#STACK_}
  _legacy_full=NEXT_PUBLIC_${_legacy}
  _new_full=NEXT_PUBLIC_${_new}
  _legacy_val=${!_legacy_full:-}
  _new_val=${!_new_full:-}
  if [ -n "$_new_val" ] && [ -z "$_legacy_val" ]; then
    export "$_legacy_full=$_new_val"
  elif [ -n "$_legacy_val" ] && [ -z "$_new_val" ]; then
    export "$_new_full=$_legacy_val"
  fi
done

export NEXT_PUBLIC_BROWSER_STACK_DASHBOARD_URL=${NEXT_PUBLIC_STACK_DASHBOARD_URL}
export NEXT_PUBLIC_HEXCLAVE_PORT_PREFIX=${NEXT_PUBLIC_HEXCLAVE_PORT_PREFIX:-${NEXT_PUBLIC_HEXCLAVE_PORT_PREFIX:-81}}
PORT_PREFIX=${NEXT_PUBLIC_HEXCLAVE_PORT_PREFIX}
export NEXT_PUBLIC_SERVER_STACK_DASHBOARD_URL="http://localhost:${PORT_PREFIX}01"
export NEXT_PUBLIC_BROWSER_STACK_API_URL=${NEXT_PUBLIC_STACK_API_URL}
export NEXT_PUBLIC_SERVER_STACK_API_URL="http://localhost:${PORT_PREFIX}02"
export BACKEND_PORT=${BACKEND_PORT:-${PORT_PREFIX}02}
export DASHBOARD_PORT=${DASHBOARD_PORT:-${PORT_PREFIX}01}
export USE_INLINE_ENV_VARS=true

if [ -z "${NEXT_PUBLIC_STACK_SVIX_SERVER_URL}" ]; then
  export NEXT_PUBLIC_STACK_SVIX_SERVER_URL=${STACK_SVIX_SERVER_URL}
fi

# ============= PATCH: Make ClickHouse optional in db-migrations.mjs =============
echo "Patching db-migrations.mjs to make ClickHouse optional..."
cd /app/apps/backend
node -e "
const fs = require('fs');
let code = fs.readFileSync('dist/db-migrations.mjs', 'utf-8');
// Patch: make createClickhouseClient handle missing env vars gracefully
code = code.replace(
  /getEnvVariable\('STACK_CLICKHOUSE_URL'\)/g,
  \"process.env['STACK_CLICKHOUSE_URL'] || ''\"
);
code = code.replace(
  /getEnvVariable\('STACK_CLICKHOUSE_ADMIN_PASSWORD'\)/g,
  \"process.env['STACK_CLICKHOUSE_ADMIN_PASSWORD'] || ''\"
);
// Patch: skip clickhouse if URL is empty
code = code.replace(
  /const clickhouseClient = createClickhouseClient\(\);/g,
  'const clickhouseClient = process.env.STACK_CLICKHOUSE_URL ? createClickhouseClient() : null;'
);
fs.writeFileSync('dist/db-migrations.mjs', code);
console.log('ClickHouse patched successfully.');
"
cd /
# ============= PATCH: Fix duplicate /api/v1 pathing bug =============
echo "Patching server.js to fix duplicate /api/v1 pathing..."
cat << 'EOF' > /tmp/patch_server.js
const fs = require('fs');

function patchServerFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // 1. 先将内容还原成未打补丁的状态（如果有旧补丁）
  const restoreRegex = /require\('next'\);?[\s\S]*?(const\s+\{\s*startServer\s*\}\s*=\s*require\('next\/dist\/server\/lib\/start-server'\))/;
  if (restoreRegex.test(content)) {
    console.log('Restoring ' + filePath + ' to original state before patching...');
    content = content.replace(restoreRegex, "require('next');\n\n$1");
  }

  // 2. 写入最新的完整补丁
  const target = "require('next');";
  const replacement = `require('next');

// ============= PATCH: Global ClickHouse client Hijacker =============
const moduleAlias = require('module');
const originalRequire = moduleAlias.prototype.require;
moduleAlias.prototype.require = function(...args) {
  const name = args[0];
  const exported = originalRequire.apply(this, args);
  if (name === '@clickhouse/client') {
    if (!exported.__isMocked) {
      exported.__isMocked = true;
      const originalCreateClient = exported.createClient;
      exported.createClient = function(...clientArgs) {
        const client = originalCreateClient.apply(this, clientArgs);
        client.query = async function() {
          return {
            json: async () => [],
            text: async () => "",
            stream: () => {
              const { Readable } = require('stream');
              return Readable.from([]);
            },
            close: () => {}
          };
        };
        client.insert = async function() { return {}; };
        client.exec = async function() { return {}; };
        client.ping = async function() { return { success: true }; };
        return client;
      };
    }
  }
  
  if (name === '@radix-ui/react-tooltip') {
    if (!exported.__isMocked) {
      exported.__isMocked = true;
      try {
        const React = require('react');
        const OriginalRoot = exported.Root || exported.Tooltip;
        const TooltipProvider = exported.Provider || exported.TooltipProvider;
        if (OriginalRoot && TooltipProvider) {
          const MockedRoot = function(props) {
            return React.createElement(TooltipProvider, {}, React.createElement(OriginalRoot, props));
          };
          Object.assign(MockedRoot, OriginalRoot);
          exported.Root = MockedRoot;
          exported.Tooltip = MockedRoot;
        }
      } catch (err) {}
    }
  }
  return exported;
};

// ============= PATCH: Start local mock ClickHouse server on port 8123 =============
try {
  const httpForMock = require('http');
  const mockClickHouse = httpForMock.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end('[]');
  });
  mockClickHouse.listen(8123, '0.0.0.0', () => {
    console.log('Mock ClickHouse Server listening on port 8123');
  });
  mockClickHouse.on('error', (err) => {
    console.log('Mock ClickHouse server error:', err.message);
  });
} catch (e) {
  console.log('Failed to start Mock ClickHouse server:', e);
}


const http = require('http');
const originalCreateServer = http.createServer;
http.createServer = function(...args) {
  const originalListener = args[args.length - 1];
  if (typeof originalListener === 'function') {
    args[args.length - 1] = function(req, res) {

      if (req.url && req.url.includes('/api/v1/api/v1')) {
        req.url = req.url.replace('/api/v1/api/v1', '/api/v1');
      }
      
      const parsedUrl = req.url ? req.url.split('?')[0] : '';
      if (req.method === 'GET' && (
        parsedUrl === '/api/v1/internal/metrics' || 
        parsedUrl === '/api/latest/internal/metrics'
      )) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          liveUsers: 0,
          dailyActiveUsers: [],
          monthlyActiveUsers: [],
          eventsCount: 0,
          totalUsers: 0
        }));
        return;
      }
      if (req.method === 'GET' && (
        parsedUrl === '/api/v1/internal/projects-metrics' ||
        parsedUrl === '/api/latest/internal/projects-metrics'
      )) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          projects: []
        }));
        return;
      }
      if (req.method === 'GET' && (
        parsedUrl === '/api/v1/internal/metrics/user-counts' ||
        parsedUrl === '/api/latest/internal/metrics/user-counts'
      )) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          liveUsers: 0,
          activeUsers: 0,
          totalUsers: 0
        }));
        return;
      }

      return originalListener(req, res);
    };
  }
  return originalCreateServer.apply(http, args);
};
`;

  content = content.replace(target, replacement);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Patched ' + filePath + ' successfully.');
}

for (const server_file of ['/app/apps/backend/server.js', '/app/apps/dashboard/server.js']) {
  if (fs.existsSync(server_file)) {
    patchServerFile(server_file);
  }
}
EOF
node /tmp/patch_server.js
rm -f /tmp/patch_server.js

# ============= PATCH: Fix Prisma \$replica inside transaction bug =============
echo "Patching Prisma \$replica in transactions..."
cat << 'EOF' > /tmp/patch_replica.js
const fs = require('fs');
const path = require('path');

function patchFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  const regex = /if\(\!\("\$transaction"in\s+(\w+)&&\s*"function"==\s*typeof\s+\1\.\$transaction\)\)throw\s+Error\("Cannot use \$replica inside of a transaction"\);?/g;
  
  if (regex.test(content)) {
    regex.lastIndex = 0;
    content = content.replace(regex, 'if(!("$transaction"in $1&&"function"==typeof $1.$transaction))return $1;');
    fs.writeFileSync(filePath, content, 'utf8');
    console.log('Patched $replica inside transaction error in:', filePath);
  }
}

function walk(dir) {
  if (!fs.existsSync(dir)) return;
  fs.readdirSync(dir).forEach(file => {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      walk(fullPath);
    } else if (file.endsWith('.js') || file.endsWith('.mjs')) {
      patchFile(fullPath);
    }
  });
}

walk('/app/apps/backend/.next');
walk('/app/apps/dashboard/.next');
EOF
node /tmp/patch_replica.js
rm -f /tmp/patch_replica.js

# ============= PATCH: Mock ClickHouse internal metrics routes =============
echo "Mocking ClickHouse internal metrics routes..."
cat << 'EOF' > /tmp/patch_metrics.js
const fs = require('fs');

function mockMetricsRoute(filePath, moduleId, defaultBody) {
  if (!fs.existsSync(filePath)) {
    console.log('File not found:', filePath);
    return;
  }
  let content = fs.readFileSync(filePath, 'utf8');
  if (content.includes('new Response(')) {
    console.log('Already mocked:', filePath);
    return;
  }
  const patch = `
const originalExports = R.m(${moduleId}).exports;
Object.defineProperty(originalExports, 'GET', {
  value: async function(request) {
    return new Response(JSON.stringify(${JSON.stringify(defaultBody)}), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  },
  writable: true,
  configurable: true,
  enumerable: true
});
module.exports = originalExports;
`;
  content += patch;
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Successfully mocked route:', filePath);
}

mockMetricsRoute(
  '/app/apps/backend/.next/server/app/api/latest/internal/metrics/route.js',
  20194,
  {
    liveUsers: 0,
    dailyActiveUsers: [],
    monthlyActiveUsers: [],
    eventsCount: 0,
    totalUsers: 0
  }
);

mockMetricsRoute(
  '/app/apps/backend/.next/server/app/api/latest/internal/projects-metrics/route.js',
  530551,
  {
    projects: []
  }
);

mockMetricsRoute(
  '/app/apps/backend/.next/server/app/api/latest/internal/metrics/user-counts/route.js',
  55701,
  {
    liveUsers: 0,
    activeUsers: 0,
    totalUsers: 0
  }
);
EOF
node /tmp/patch_metrics.js
rm -f /tmp/patch_metrics.js

# ============= MIGRATIONS =============
should_run_migrations=true
if [ "$STACK_SKIP_MIGRATIONS" = "true" ] || [ "$STACK_RUN_MIGRATIONS" = "false" ]; then
  should_run_migrations=false
fi

if [ "$should_run_migrations" = "false" ]; then
  echo "Skipping migrations."
else
  echo "Running migrations..."
  cd /app/apps/backend
  node dist/db-migrations.mjs migrate || echo "Migration completed (ClickHouse warnings ignored)."
  cd /
fi

should_run_seed_script=true
if [ "$STACK_SKIP_SEED_SCRIPT" = "true" ] || [ "$STACK_RUN_SEED_SCRIPT" = "false" ]; then
  should_run_seed_script=false
fi

if [ "$should_run_seed_script" = "false" ]; then
  echo "Skipping seed script."
else
  echo "Running seed script..."
  cd /app/apps/backend
  node dist/db-migrations.mjs seed || echo "Seed completed (ClickHouse warnings ignored)."
  cd /
fi

# ============= LOCAL EMULATOR: BOOTSTRAP =============
if [ "$NEXT_PUBLIC_STACK_IS_LOCAL_EMULATOR" = "true" ] && [ -n "${STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY:-}" ] && [ -n "${STACK_DATABASE_CONNECTION_STRING:-}" ]; then
  for varname in STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY; do
    val="${!varname:-}"
    if [ -z "$val" ]; then echo "ERROR: $varname is not set; refusing to bootstrap." >&2; exit 1; fi
    if ! printf '%s' "$val" | grep -Eq '^[0-9a-fA-F]+$'; then echo "ERROR: $varname is not hex-only." >&2; exit 1; fi
  done
  echo "Bootstrapping internal API key set (emulator runtime)..."
  psql "$STACK_DATABASE_CONNECTION_STRING" -v ON_ERROR_STOP=1 <<SQL
INSERT INTO "ApiKeySet" ("projectId", id, description, "expiresAt", "createdAt", "updatedAt", "publishableClientKey", "secretServerKey", "superSecretAdminKey")
VALUES ('internal', '3142e763-b230-44b5-8636-aa62f7489c26', 'Internal API key set', '2099-12-31T23:59:59Z', NOW(), NOW(),
        '${STACK_INTERNAL_PROJECT_PUBLISHABLE_CLIENT_KEY}',
        '${STACK_INTERNAL_PROJECT_SECRET_SERVER_KEY}',
        '${STACK_SEED_INTERNAL_PROJECT_SUPER_SECRET_ADMIN_KEY}')
ON CONFLICT ("projectId", id) DO UPDATE SET
  "publishableClientKey" = EXCLUDED."publishableClientKey",
  "secretServerKey" = EXCLUDED."secretServerKey",
  "superSecretAdminKey" = EXCLUDED."superSecretAdminKey",
  "updatedAt" = NOW();
SQL
fi

# ============= ENV VARS & SENTINEL REPLACEMENT =============
WORK_DIR="${STACK_RUNTIME_WORK_DIR:-/app}"
SENTINEL_MARKER="/tmp/.stack-sentinels-replaced"

echo "Using working directory: $WORK_DIR"

SENTINEL_MARKER="${SENTINEL_MARKER:-/tmp/.stack-sentinels-replaced}"
if [ -f "$SENTINEL_MARKER" ]; then
  echo "Sentinels already replaced; skipping scan."
else
  echo "Finding unhandled sentinels..."
  unhandled_sentinels=$(find "$WORK_DIR/apps" -type f -exec grep -l "STACK_ENV_VAR_SENTINEL" {} + | \
    xargs grep -h "STACK_ENV_VAR_SENTINEL" | \
    grep -oE "STACK_ENV_VAR_SENTINEL_[A-Z_]*[A-Z]+[A-Z_]*" | \
    sort -u)
  delimiter=$(printf '\037')
  echo "Replacing sentinels..."
  for sentinel in $unhandled_sentinels; do
    env_var=${sentinel#STACK_ENV_VAR_SENTINEL_}
    if [ -z "$env_var" ]; then continue; fi
    value="${!env_var}"
    if [ -z "$value" ]; then continue; fi
    escaped_sentinel=$(printf '%s\n' "$sentinel" | sed -e 's/\\/\\\\/g' -e 's/[][\/.^$*]/\\&/g')
    escaped_value=$(printf '%s\n' "$value" | sed -e 's/\\/\\\\/g' -e "s/[${delimiter}&]/\\\\&/g")
    files=$(grep -rl "$sentinel" "$WORK_DIR/apps" 2>/dev/null || true)
    if [ -n "$files" ]; then
      echo "$files" | xargs sed -i "s${delimiter}${escaped_sentinel}${delimiter}${escaped_value}${delimiter}g"
    fi
  done
  echo "Sentinel replacement complete."
  touch "$SENTINEL_MARKER"
fi

# ============= START BACKEND AND DASHBOARD =============
echo "Starting backend on port $BACKEND_PORT..."
cd "$WORK_DIR"
PORT=$BACKEND_PORT HOSTNAME=0.0.0.0 node apps/backend/server.js &

echo "Starting dashboard on port $DASHBOARD_PORT..."
PORT=$DASHBOARD_PORT HOSTNAME=0.0.0.0 node apps/dashboard/server.js &

wait -n
