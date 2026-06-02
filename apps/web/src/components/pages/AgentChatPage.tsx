import ChatLayout from '../chat/ChatLayout';
import { ChatProvider } from '../../store/sessions';

export function AgentChatPage() {
  return (
    <div data-testid="page-agent-chat" style={{ height: '100%' }}>
      <ChatProvider>
        <ChatLayout />
      </ChatProvider>
    </div>
  );
}

export default AgentChatPage;
