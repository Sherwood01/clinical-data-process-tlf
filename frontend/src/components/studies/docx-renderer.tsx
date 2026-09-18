"use client";

import { useEffect, useRef } from "react";
import * as docx from "docx-preview";

interface DocxRendererProps {
  blob: Blob;
}

/**
 * 客户端 Docx 渲染组件。
 * 该组件专门在客户端动态导入（ssr: false），用于避免服务端渲染期间没有 window/document 对象造成的报错，
 * 同时以静态导入方式引入 docx-preview，确保 Next.js 生产环境打包能完美将其打入包内。
 *
 * 参数:
 *   blob: 要渲染的 Word 文档的 Blob 二进制数据。
 */
export default function DocxRenderer({ blob }: DocxRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!blob || !containerRef.current) return;

    let isSubscribed = true;
    const container = containerRef.current;
    container.innerHTML = "";

    const renderDocx = async () => {
      try {
        const renderAsync = docx.renderAsync || (docx as any).default?.renderAsync;
        if (!renderAsync) {
          throw new Error("docx-preview 中的 renderAsync 方法未定义。");
        }
        if (isSubscribed && container) {
          await renderAsync(blob, container, undefined, {
            className: "docx",
            inWrapper: true,
            ignoreWidth: false,
            ignoreHeight: false,
          });
        }
      } catch (err) {
        console.error("Failed to render docx:", err);
        if (isSubscribed && container) {
          container.innerHTML = `<div class="p-6 text-red-500 font-semibold">渲染 Word 文档失败: ${(err as Error).message}。请下载后查看。</div>`;
        }
      }
    };

    renderDocx();

    return () => {
      isSubscribed = false;
      if (container) {
        container.innerHTML = "";
      }
    };
  }, [blob]);

  return (
    <div 
      ref={containerRef} 
      className="bg-gray-200/50 flex-1 overflow-auto rounded-lg border p-6 shadow-inner flex justify-center w-full h-full"
    />
  );
}
