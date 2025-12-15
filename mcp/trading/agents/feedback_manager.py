"""
Feedback Manager for ApexAI Aura Insight
Handles storage and retrieval of user feedback for signal validation and learning.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class FeedbackManager:
    """
    Manages user feedback for trading signals.
    Stores feedback data for analysis and model improvement.
    """

    def __init__(self, storage_path: str = "feedback_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.feedback_file = self.storage_path / "feedback.json"
        self._load_feedback_data()

    def _load_feedback_data(self):
        """Load feedback data from storage."""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    self.feedback_data = json.load(f)
            except json.JSONDecodeError:
                self.feedback_data = {}
        else:
            self.feedback_data = {}

    def _save_feedback_data(self):
        """Save feedback data to storage."""
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=2, default=str)

    def store_feedback(self, workflow_id: str, feedback: str, comments: Optional[str] = None) -> bool:
        """
        Store user feedback for a workflow.

        Args:
            workflow_id: Unique workflow identifier
            feedback: "good_signal" or "bad_signal"
            comments: Optional user comments

        Returns:
            True if feedback was stored successfully
        """
        try:
            feedback_entry = {
                "workflow_id": workflow_id,
                "feedback": feedback,
                "comments": comments,
                "timestamp": datetime.now().isoformat(),
                "processed": False  # For future learning pipeline
            }

            self.feedback_data[workflow_id] = feedback_entry
            self._save_feedback_data()

            print(f"✅ Feedback stored for workflow {workflow_id}: {feedback}")
            return True

        except Exception as e:
            print(f"❌ Error storing feedback: {e}")
            return False

    def get_feedback(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve feedback for a specific workflow.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            Feedback data or None if not found
        """
        return self.feedback_data.get(workflow_id)

    def get_all_feedback(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all stored feedback.

        Returns:
            Dictionary of all feedback entries
        """
        return self.feedback_data.copy()

    def get_recent_feedback(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get feedback from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of recent feedback entries
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_feedback = []

        for feedback in self.feedback_data.values():
            feedback_timestamp = datetime.fromisoformat(feedback["timestamp"]).timestamp()
            if feedback_timestamp >= cutoff_date:
                recent_feedback.append(feedback)

        return recent_feedback

    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored feedback.

        Returns:
            Dictionary with feedback statistics
        """
        total_feedback = len(self.feedback_data)
        good_signals = sum(1 for f in self.feedback_data.values() if f["feedback"] == "good_signal")
        bad_signals = sum(1 for f in self.feedback_data.values() if f["feedback"] == "bad_signal")

        recent_feedback = self.get_recent_feedback(days=7)
        recent_good = sum(1 for f in recent_feedback if f["feedback"] == "good_signal")
        recent_bad = sum(1 for f in recent_feedback if f["feedback"] == "bad_signal")

        return {
            "total_feedback": total_feedback,
            "good_signals": good_signals,
            "bad_signals": bad_signals,
            "good_signal_percentage": (good_signals / total_feedback * 100) if total_feedback > 0 else 0,
            "recent_feedback_7d": len(recent_feedback),
            "recent_good_signals": recent_good,
            "recent_bad_signals": recent_bad,
            "recent_accuracy": (recent_good / len(recent_feedback) * 100) if recent_feedback else 0
        }

    def mark_feedback_processed(self, workflow_id: str) -> bool:
        """
        Mark feedback as processed for learning pipeline.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            True if successfully marked as processed
        """
        if workflow_id in self.feedback_data:
            self.feedback_data[workflow_id]["processed"] = True
            self._save_feedback_data()
            return True
        return False

    def get_unprocessed_feedback(self) -> List[Dict[str, Any]]:
        """
        Get feedback that hasn't been processed for learning.

        Returns:
            List of unprocessed feedback entries
        """
        return [f for f in self.feedback_data.values() if not f.get("processed", False)]

    def export_feedback_for_learning(self, output_path: str) -> bool:
        """
        Export feedback data for model learning pipeline.

        Args:
            output_path: Path to export the data

        Returns:
            True if export was successful
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "feedback_data": self.feedback_data,
                "stats": self.get_feedback_stats()
            }

            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"✅ Feedback data exported to {output_path}")
            return True

        except Exception as e:
            print(f"❌ Error exporting feedback data: {e}")
            return False

# Global feedback manager instance
feedback_manager = FeedbackManager()

def get_feedback_manager() -> FeedbackManager:
    """Get the global feedback manager instance."""
    return feedback_manager

# Example usage and testing
if __name__ == "__main__":
    # Test the feedback manager
    fm = FeedbackManager()

    # Store some test feedback
    test_workflows = [
        ("signal_SPY_20241201_120000", "good_signal", "Accurate signal, good entry timing"),
        ("signal_QQQ_20241201_120500", "bad_signal", "False positive, market went opposite"),
        ("signal_AAPL_20241201_121000", "good_signal", None),
    ]

    for workflow_id, feedback, comments in test_workflows:
        fm.store_feedback(workflow_id, feedback, comments)

    # Get stats
    stats = fm.get_feedback_stats()
    print("Feedback Statistics:")
    print(json.dumps(stats, indent=2))

    # Export for learning
    fm.export_feedback_for_learning("feedback_export.json")