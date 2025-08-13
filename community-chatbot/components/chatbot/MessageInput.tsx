import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Paperclip, Send, StopCircle } from "lucide-react"
import type { UseChatHelpers } from "@ai-sdk/react"

interface MessageInputProps extends Pick<UseChatHelpers, "input" | "handleInputChange" | "handleSubmit" | "status" | "stop"> {
  currentModeName: string | undefined
}

export function MessageInput({
  input,
  handleInputChange,
  handleSubmit,
  status,
  stop,
  currentModeName,
}: MessageInputProps) {
  return (
    <div className="bg-white dark:bg-gray-800 p-4 dark:border-gray-700 border-t">
      <div className="mx-auto max-w-4xl">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Input
              value={input}
              onChange={handleInputChange}
              placeholder={`Ask ${currentModeName || "the assistant"}...`}
              disabled={status !== "ready"}
              autoFocus
            />
          </div>

          {status === "streaming" ? (
            <Button type="button" variant="outline" size="icon" onClick={() => stop()}>
              <StopCircle className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || status !== "ready"}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Send className="w-4 h-4" />
            </Button>
          )}
        </form>
      </div>
    </div>
  )
}