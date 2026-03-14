/**
 * @jest-environment node
 */

import { POST } from '@/app/api/chat/route';
import { handleGeneralRequest } from '@/app/api/chat/handlers/general';
import { handleGitHubRequest } from '@/app/api/chat/handlers/github';
import { handleJiraRequest } from '@/app/api/chat/handlers/jira';
import { handleSlackRequest } from '@/app/api/chat/handlers/slack';

// Mock the handlers
jest.mock('@/app/api/chat/handlers/general');
jest.mock('@/app/api/chat/handlers/github');
jest.mock('@/app/api/chat/handlers/jira');
jest.mock('@/app/api/chat/handlers/slack');

// Mock @ai-sdk/openai
jest.mock('@ai-sdk/openai', () => ({
    openai: jest.fn().mockReturnValue('mock-openai'),
}));

// Mock constants
jest.mock('@/app/api/chat/lib/constants', () => ({
    SYSTEM_PROMPTS: {
        general: 'Mock general prompt',
    },
    maxDuration: 30,
}));

describe('Chat API route', () => {
    const originalResponse = global.Response;

    beforeEach(() => {
        jest.clearAllMocks();

        // Custom MockResponse to handle body reading in tests
        class MockResponse {
            status: number;
            headers: Map<string, string>;
            body: any;

            constructor(body: any, init?: any) {
                this.body = body;
                this.status = init?.status || 200;
                this.headers = new Map(Object.entries(init?.headers || {}));
            }

            async json() {
                return JSON.parse(this.body);
            }

            async text() {
                return String(this.body);
            }
        }
        global.Response = MockResponse as any;
    });

    afterAll(() => {
        global.Response = originalResponse;
    });

    const createRequest = (body: any) => {
        return new Request('https://localhost:3000/api/chat', {
            method: 'POST',
            body: JSON.stringify(body),
            headers: {
                'Content-Type': 'application/json',
            },
        });
    };

    describe('Validation', () => {
        it('should return 400 if messages is missing', async () => {
            const req = createRequest({ mode: 'general' });
            const res = await POST(req);
            expect(res.status).toBe(400);
            const data = await res.json();
            expect(data.error).toBe("Request must contain a 'messages' array.");
        });

        it('should return 400 if mode is missing', async () => {
            const req = createRequest({ messages: [{ id: '1', role: 'user', content: 'hi', timestamp: Date.now() }] });
            const res = await POST(req);
            expect(res.status).toBe(400);
            const data = await res.json();
            expect(data.error).toBe("Request must contain a 'mode' string.");
        });

        it('should return 400 if messages is empty', async () => {
            const req = createRequest({ messages: [], mode: 'general' });
            const res = await POST(req);
            expect(res.status).toBe(400);
            const data = await res.json();
            expect(data.error).toBe("Request must contain a non-empty messages array.");
        });

        it('should return 400 if last message is not from user', async () => {
            const req = createRequest({
                messages: [{ id: '1', role: 'assistant', content: 'hi', timestamp: Date.now() }],
                mode: 'general'
            });
            const res = await POST(req);
            expect(res.status).toBe(400);
            const data = await res.json();
            expect(data.error).toBe("Invalid message sequence. The last message must be from a user.");
        });
    });

    describe('Modes', () => {
        const messages = [{ id: '1', role: 'user' as const, content: 'test query', timestamp: Date.now() }];

        it('should call handleSlackRequest for slack mode', async () => {
            const req = createRequest({ messages, mode: 'slack' });
            await POST(req);
            expect(handleSlackRequest).toHaveBeenCalledWith('test query');
        });

        it('should call handleJiraRequest for jira mode', async () => {
            const req = createRequest({ messages, mode: 'jira' });
            await POST(req);
            expect(handleJiraRequest).toHaveBeenCalledWith('test query');
        });

        it('should call handleGitHubRequest for github mode', async () => {
            const req = createRequest({ messages, mode: 'github' });
            await POST(req);
            expect(handleGitHubRequest).toHaveBeenCalledWith('test query');
        });

        it('should call handleGeneralRequest for unknown mode', async () => {
            const req = createRequest({ messages, mode: 'unknown' });
            await POST(req);
            expect(handleGeneralRequest).toHaveBeenCalledWith(messages);
        });
    });

    describe('Error Handling', () => {
        const messages = [{ id: '1', role: 'user' as const, content: 'test query', timestamp: Date.now() }];

        it('should fall back to general request if integration handler fails', async () => {
            (handleJiraRequest as jest.Mock).mockRejectedValue(new Error('Jira Down'));
            const req = createRequest({ messages, mode: 'jira' });

            await POST(req);

            expect(handleGeneralRequest).toHaveBeenCalled();
            const calledWithMessages = (handleGeneralRequest as jest.Mock).mock.calls[0][0];
            expect(calledWithMessages[0].content).toContain('I was trying to use the jira integration but it seems to be unavailable');
        });

        it('should return 500 if a critical error occurs', async () => {
            // Force an error during JSON parsing or something else critical
            const req = new Request('https://localhost:3000/api/chat', {
                method: 'POST',
                body: 'invalid-json',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const res = await POST(req);
            expect(res.status).toBe(500);
            const data = await res.json();
            expect(data.error).toContain('An unexpected server error occurred');
        });

        it('should return 500 if the general handler fails (e.g. missing API keys)', async () => {
            (handleGeneralRequest as jest.Mock).mockRejectedValue(new Error('Missing OpenAI API Key'));
            const req = createRequest({ messages, mode: 'general' });

            const res = await POST(req);
            expect(res.status).toBe(500);
            const data = await res.json();
            expect(data.error).toContain('An unexpected server error occurred');
        });
    });
});
