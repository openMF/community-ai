import {
  MessageInput,
} from '@/components/agent/Mode/Chat/InputBox/MessageInput';
import {
  SubmitButton,
} from '@/components/agent/Mode/Chat/InputBox/SubmitButton';
import { useSendMessage } from '@/hooks/agent/Mode/Chat/useSendMessage';

export function InputBox() {
  const { handleSendMessage } = useSendMessage();
  const handleSubmit = async (event?: React.FormEvent) => {
    if (event) event.preventDefault();
    handleSendMessage()
  };

  return (
    <div className="bg-white dark:bg-gray-800 p-4 dark:border-gray-700 border-t">
      <div className="mx-auto max-w-4xl">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <MessageInput />
          <SubmitButton />
        </form>
      </div>
    </div>
  );
}
