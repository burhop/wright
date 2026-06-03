import WorkspacePanel from './WorkspacePanel';

export function ChatLayout() {
  return (
    <div data-testid="chat-layout" style={{ height: '100%', width: '100%', overflow: 'hidden' }}>
      <WorkspacePanel />
    </div>
  );
}

export default ChatLayout;
