import logging
import time
from datetime import datetime, timedelta
from typing import List

# Import the consolidated tools
from tools.mifos_tools import (
    get_repo_overview,
    get_pr_details,
    check_ci_status,
    get_issue_context,
    search_messages,
    produce_mifos_summary,
    add_to_knowledge_base,
    get_settings
)

logger = logging.getLogger(__name__)

class MifosWatchdog:
    def __init__(self):
        self.settings = get_settings()
        self.last_check = datetime.now() - timedelta(hours=24)
        # The channel where daily technical summaries are posted
        self.report_channel = self.settings.SLACK_REPORT_CHANNEL 

    def run_daily_sync(self):
        """
        The core loop: 
        1. Scans GitHub for PRs.
        2. Gathers Jira/Slack context.
        3. Generates a 'Librarian' summary.
        4. Saves the summary to the Knowledge Base (RAG).
        """
        logger.info("🚀 Starting Daily Mifos Watchdog Sync...")

        try:
            # 1. Get Repo Activity
            # We use 'recent updates' as the query for the summary tool
            github_activity = get_repo_overview("Summarize all activity in the last 24 hours")
            
            # 2. Deep Dive into failing CI (Proactive Lead logic)
            ci_report = check_ci_status()
            
            # 3. Combine context for the Librarian
            # We fetch recent Slack consensus to see why certain decisions were made
            slack_context = search_messages("release consensus")
            
            full_context = f"""
            GITHUB ACTIVITY:
            {github_activity}
            
            CI STATUS:
            {ci_report}
            
            SLACK DISCUSSIONS:
            {slack_context}
            """

            # 4. Produce the professional Documentation/Summary
            report_title = f"Daily Technical Sync: {datetime.now().strftime('%Y-%m-%d')}"
            result = produce_mifos_summary(
                channel_id=self.report_channel,
                title=report_title,
                raw_context=full_context,
                is_draft=False # Official report
            )

            # 5. Permanent Memory: Add this report to the Knowledge Base
            # This allows future queries to find 'what happened on this date'
            add_to_knowledge_base(
                documents=[full_context],
                metadata=[{"source": "watchdog", "date": str(datetime.now().date())}]
            )

            logger.info(f"✅ Watchdog Sync Complete: {result}")

        except Exception as e:
            logger.error(f"❌ Watchdog Sync Failed: {str(e)}")

    def monitor_loop(self):
        """Polls every hour, but only runs the full sync once a day."""
        while True:
            now = datetime.now()
            # Run at 9:00 AM every day
            if now.hour == 9 and self.last_check.date() < now.date():
                self.run_daily_sync()
                self.last_check = now
            
            time.sleep(3600) # Check every hour

if __name__ == "__main__":
    watchdog = MifosWatchdog()
    # For initial testing, run once immediately
    watchdog.run_daily_sync()
    watchdog.monitor_loop()