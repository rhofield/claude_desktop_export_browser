#!/usr/bin/env python3
import argparse
import json
import os
import sys
import datetime
from typing import List, Dict, Any, Optional
import curses

class ClaudeChatBrowser:
    def __init__(self, data_dir: str, output_format: str = "both"):
        self.data_dir = data_dir
        self.output_format = output_format
        self.conversations = []
        self.conversations_path = os.path.join(data_dir, "conversations.json")
        self.page_size = 10
        self.current_page = 0
        self.export_dir = os.path.join(os.path.dirname(data_dir), "exports")
        
        # Create exports directory if it doesn't exist
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
        
        self.load_conversations()
        
    def load_conversations(self):
        """Load conversations from the JSON file."""
        try:
            with open(self.conversations_path, 'r') as f:
                self.conversations = json.load(f)
                
            # Sort by updated_at timestamp (most recent first)
            self.conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        except Exception as e:
            print(f"Error loading conversations: {str(e)}")
            sys.exit(1)
            
    def get_total_pages(self) -> int:
        """Calculate the total number of pages."""
        return (len(self.conversations) + self.page_size - 1) // self.page_size
    
    def get_current_page_conversations(self) -> List[Dict[str, Any]]:
        """Get conversations for the current page."""
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        return self.conversations[start_idx:end_idx]
    
    def format_conversation_title(self, conversation: Dict[str, Any]) -> str:
        """Format a conversation for display in the list."""
        # Use conversation name if available, otherwise use the first message text
        name = conversation.get('name', '')
        if not name and 'chat_messages' in conversation and conversation['chat_messages']:
            for msg in conversation['chat_messages']:
                if msg.get('sender') == 'human' and msg.get('text'):
                    name = msg.get('text', '')[:50]
                    if name:
                        break
                        
        # Fallback if still no name
        if not name:
            name = "Untitled conversation"
            
        # Format date
        date_str = "No date"
        if 'updated_at' in conversation:
            try:
                date = datetime.datetime.fromisoformat(conversation['updated_at'].replace('Z', '+00:00'))
                date_str = date.strftime("%Y-%m-%d %H:%M")
            except:
                pass
                
        # Count messages
        msg_count = len(conversation.get('chat_messages', []))
        
        return f"{date_str} | {msg_count} msgs | {name}"
    
    def export_conversation(self, conversation: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Export a conversation and return exported markdown/json paths (or None when skipped)."""
        # Create a filename based on date and name or ID
        name = conversation.get('name', '') or "conversation"
        name = ''.join(c if c.isalnum() or c in ' _-' else '_' for c in name).strip()
        date_str = "unknown_date"
        if 'updated_at' in conversation:
            try:
                date = datetime.datetime.fromisoformat(conversation['updated_at'].replace('Z', '+00:00'))
                date_str = date.strftime("%Y%m%d_%H%M%S")
            except:
                pass
        
        # Ensure name is not too long for a filename
        if len(name) > 50:
            name = name[:47] + "..."
            
        # Create file paths
        md_filename = f"{date_str}_{name}.md"
        json_filename = f"{date_str}_{name}.json"
        md_file_path = os.path.join(self.export_dir, md_filename)
        json_file_path = os.path.join(self.export_dir, json_filename)
        
        # Create a copy of the conversation to sort messages by date
        export_conversation = conversation.copy()
        
        # Sort messages by creation date
        if 'chat_messages' in export_conversation:
            sorted_messages = sorted(
                export_conversation['chat_messages'], 
                key=lambda x: x.get('created_at', '0')
            )
            export_conversation['chat_messages'] = sorted_messages
        
        # Format conversation as markdown
        markdown = [f"# {name or 'Claude Chat Conversation'}\n"]
        markdown.append(f"Date: {date_str}\n")
        markdown.append(f"ID: {conversation.get('uuid', 'Unknown')}\n\n")
        
        # Add messages
        for msg in export_conversation.get('chat_messages', []):
            sender = "**User**:" if msg.get('sender') == 'human' else "**Claude**:"
            text = msg.get('text', '')
            
            # If no text directly available, try to get it from content
            if not text and 'content' in msg:
                for content_item in msg['content']:
                    if content_item.get('type') == 'text':
                        text = content_item.get('text', '')
                        break
            
            # Include timestamp if available
            timestamp = ""
            if msg.get('created_at'):
                try:
                    msg_date = datetime.datetime.fromisoformat(msg.get('created_at').replace('Z', '+00:00'))
                    timestamp = f"[{msg_date.strftime('%Y-%m-%d %H:%M:%S')}]"
                except:
                    pass
            
            if text:  # Only add messages with content
                if timestamp:
                    markdown.append(f"{sender} {timestamp}\n\n{text}\n\n---\n\n")
                else:
                    markdown.append(f"{sender}\n\n{text}\n\n---\n\n")
        
        exported_md_path = None
        exported_json_path = None

        if self.output_format in ("both", "md"):
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(markdown))
            exported_md_path = md_file_path

        if self.output_format in ("both", "json"):
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(export_conversation, f, indent=2, ensure_ascii=False)
            exported_json_path = json_file_path

        return exported_md_path, exported_json_path

    def export_all_conversations(self) -> tuple[int, int]:
        """Export all conversations. Returns (successful_exports, failed_exports)."""
        successful_exports = 0
        failed_exports = 0

        for conversation in self.conversations:
            try:
                self.export_conversation(conversation)
                successful_exports += 1
            except Exception as e:
                conversation_id = conversation.get('uuid', 'Unknown')
                print(f"Warning: failed to export conversation {conversation_id}: {str(e)}", file=sys.stderr)
                failed_exports += 1

        return successful_exports, failed_exports
        
    def run_ui(self):
        """Run the curses UI."""
        curses.wrapper(self._curses_main)
    
    def _curses_main(self, stdscr):
        # Set up curses
        curses.curs_set(0)  # Hide cursor
        stdscr.timeout(100)  # Non-blocking input
        stdscr.clear()
        
        # Get terminal size
        height, width = stdscr.getmaxyx()
        
        # Create color pairs
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Highlighted item
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Headers
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Navigation help
        
        # Initialize selected item
        selected_idx = 0
        
        while True:
            # Clear screen
            stdscr.clear()
            
            # Display header
            header = "CLAUDE CHAT EXPORT BROWSER"
            subheader = "Export your Claude Desktop chats"
            stdscr.addstr(0, (width - len(header)) // 2, header, curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(1, (width - len(subheader)) // 2, subheader)
            
            # Display current page info
            total_pages = self.get_total_pages()
            page_info = f"Page {self.current_page + 1}/{total_pages}"
            stdscr.addstr(2, (width - len(page_info)) // 2, page_info)
            
            # Get conversations for current page
            page_conversations = self.get_current_page_conversations()
            
            # Display conversations
            for i, conv in enumerate(page_conversations):
                y = i + 4  # Start from line 4 (after header, subheader, and page info)
                if y >= height - 3:  # Leave space for footer
                    break
                    
                title = self.format_conversation_title(conv)
                # Truncate title if too long
                if len(title) > width - 2:
                    title = title[:width - 5] + "..."
                    
                # Highlight selected item
                if i == selected_idx:
                    stdscr.addstr(y, 1, title, curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addstr(y, 1, title)
            
            # Display footer with navigation help
            footer = "↑/↓: Navigate | ←/→: Change Page | Enter: Select | q: Quit"
            stdscr.addstr(height - 2, (width - len(footer)) // 2, footer, curses.color_pair(3))
            
            # Refresh screen
            stdscr.refresh()
            
            # Handle input
            try:
                c = stdscr.getch()
                
                if c == ord('q'):
                    break
                elif c == curses.KEY_UP and selected_idx > 0:
                    selected_idx -= 1
                elif c == curses.KEY_DOWN and selected_idx < len(page_conversations) - 1:
                    selected_idx += 1
                elif c == curses.KEY_LEFT and self.current_page > 0:
                    self.current_page -= 1
                    selected_idx = 0
                elif c == curses.KEY_RIGHT and self.current_page < total_pages - 1:
                    self.current_page += 1
                    selected_idx = 0
                elif c == curses.KEY_ENTER or c == 10 or c == 13:  # Enter key
                    # Show conversation details and confirm export
                    if 0 <= selected_idx < len(page_conversations):
                        selected_conv = page_conversations[selected_idx]
                        self._show_conversation_details(stdscr, selected_conv)
            except Exception as e:
                # Handle any exceptions
                stdscr.clear()
                stdscr.addstr(0, 0, f"Error: {str(e)}")
                stdscr.refresh()
                stdscr.getch()
                
    def _show_conversation_details(self, stdscr, conversation):
        height, width = stdscr.getmaxyx()
        
        # Clear screen
        stdscr.clear()
        
        # Display header
        title = "CLAUDE CHAT EXPORT BROWSER"
        subtitle = "CONVERSATION DETAILS"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, (width - len(subtitle)) // 2, subtitle, curses.A_BOLD)
        
        # Display conversation info
        name = conversation.get('name', '') or "Untitled conversation"
        date_str = "No date"
        if 'updated_at' in conversation:
            try:
                date = datetime.datetime.fromisoformat(conversation['updated_at'].replace('Z', '+00:00'))
                date_str = date.strftime("%Y-%m-%d %H:%M")
            except:
                pass
                
        msg_count = len(conversation.get('chat_messages', []))
        
        info = [
            f"Title: {name}",
            f"Date: {date_str}",
            f"Message count: {msg_count}",
            f"ID: {conversation.get('uuid', 'Unknown')}"
        ]
        
        # Display first few messages
        messages = []
        for msg in conversation.get('chat_messages', [])[:3]:  # First 3 messages
            sender = "User:" if msg.get('sender') == 'human' else "Claude:"
            text = msg.get('text', '')
            
            # If no text directly available, try to get it from content
            if not text and 'content' in msg:
                for content_item in msg['content']:
                    if content_item.get('type') == 'text':
                        text = content_item.get('text', '')
                        break
            
            # Truncate message if too long
            if text:
                if len(text) > 100:
                    text = text[:97] + "..."
                messages.append(f"{sender} {text}")
        
        # Display conversation info and preview
        y = 3  # Start at line 3 (after headers)
        for line in info:
            stdscr.addstr(y, 2, line)
            y += 1
            
        stdscr.addstr(y + 1, 2, "Preview:", curses.A_BOLD)
        y += 2
        
        for msg in messages:
            if y >= height - 5:  # Leave space for prompt
                break
            # Wrap message if needed
            if len(msg) > width - 4:
                msg = msg[:width - 7] + "..."
            stdscr.addstr(y, 2, msg)
            y += 1
        
        # Display export prompt
        format_label = {
            "both": "Markdown and JSON",
            "md": "Markdown",
            "json": "JSON",
        }.get(self.output_format, "Markdown and JSON")
        prompt = f"Export this conversation to {format_label}? (y/n)"
        stdscr.addstr(height - 3, (width - len(prompt)) // 2, prompt, curses.color_pair(3) | curses.A_BOLD)
        
        stdscr.refresh()
        
        # Wait for user input
        while True:
            c = stdscr.getch()
            if c == ord('y') or c == ord('Y'):
                # Export conversation
                try:
                    md_path, json_path = self.export_conversation(conversation)
                    # Show success message
                    stdscr.clear()
                    
                    # Calculate center positions
                    y_center = height // 2

                    exported_messages = []
                    if md_path:
                        exported_messages.append(f"Markdown exported to: {md_path}")
                    if json_path:
                        exported_messages.append(f"JSON exported to: {json_path}")

                    start_y = y_center - (len(exported_messages) // 2)
                    for i, msg in enumerate(exported_messages):
                        stdscr.addstr(start_y + i, (width - len(msg)) // 2, msg, curses.color_pair(2))

                    stdscr.addstr(start_y + len(exported_messages) + 2, (width - 17) // 2, "Press any key...", curses.color_pair(3))
                    stdscr.refresh()
                    stdscr.getch()
                except Exception as e:
                    # Show error message
                    stdscr.clear()
                    msg = f"Error exporting conversation: {str(e)}"
                    stdscr.addstr(height // 2, (width - len(msg)) // 2, msg, curses.color_pair(1))
                    stdscr.addstr(height // 2 + 2, (width - 17) // 2, "Press any key...", curses.color_pair(3))
                    stdscr.refresh()
                    stdscr.getch()
                break
            elif c == ord('n') or c == ord('N'):
                break


def resolve_data_directory(input_path: str) -> str:
    """Resolve a CLI input path into a Claude export directory containing conversations.json."""
    absolute_path = os.path.abspath(input_path)

    if os.path.isfile(absolute_path):
        if os.path.basename(absolute_path) != "conversations.json":
            print("Error: file input must be a conversations.json file.")
            sys.exit(1)
        data_dir = os.path.dirname(absolute_path)
    elif os.path.isdir(absolute_path):
        data_dir = absolute_path
    else:
        print(f"Error: path does not exist: {absolute_path}")
        sys.exit(1)

    conversations_path = os.path.join(data_dir, "conversations.json")
    if not os.path.isfile(conversations_path):
        print(f"Error: conversations.json not found in: {data_dir}")
        sys.exit(1)

    return data_dir


def main():
    """Main entry point for the program."""
    parser = argparse.ArgumentParser(
        description="Browse Claude conversations and export them to Markdown and JSON."
    )
    parser.add_argument(
        "input_path",
        help="Path to a Claude export directory or directly to conversations.json",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Export all conversations to the exports directory without opening the UI.",
    )
    parser.add_argument(
        "--output-format",
        choices=["both", "md", "json"],
        default="both",
        help="Choose exported file format(s): both (default), md, or json.",
    )
    args = parser.parse_args()

    data_dir = resolve_data_directory(args.input_path)
    print(f"Using Claude data from: {data_dir}")

    browser = ClaudeChatBrowser(data_dir, output_format=args.output_format)
    if args.all:
        successful, failed = browser.export_all_conversations()
        print(f"Exported {successful} conversation(s) as {args.output_format} to: {browser.export_dir}")
        if failed:
            print(f"Failed exports: {failed}", file=sys.stderr)
            sys.exit(1)
        return

    print("Starting browser interface...")
    browser.run_ui()


if __name__ == "__main__":
    main()
