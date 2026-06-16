import { redirect } from "next/navigation";

export default function TLFIntermediatePage({ params }: { params: { studyId: string } }) {
  redirect(`/studies/${params.studyId}`);
}
