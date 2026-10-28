import { createContext, useContext, type ReactNode } from "react";

export type FileDownloadResult = "requested" | "declined" | "unavailable";
export type FileDownloadRequest = (blob: Blob, name: string) => Promise<FileDownloadResult>;
const DownloadContext = createContext<FileDownloadRequest | undefined>(undefined);

/** Host delivery only. File scope, bytes and evidence remain with their owners. */
export function FileDownloadProvider({ request, children }: {
  request: FileDownloadRequest;
  children: ReactNode;
}) {
  return <DownloadContext.Provider value={request}>{children}</DownloadContext.Provider>;
}
export function useFileDownload() { return useContext(DownloadContext); }
export function fileDownloadMessage(result: FileDownloadResult) {
  if (result === "unavailable") return "This desktop does not support file downloads from this panel.";
  if (result === "declined") return "The desktop cancelled or declined the download.";
  return "Download requested. Check the desktop’s save dialog or Downloads folder.";
}
