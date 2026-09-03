
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from apps.wallet.models import TransactionType, TransactionStatus



import re


def normalize_text(text):
    text = text.lower().strip()

    text = re.sub(
        r"[^\w\s]",
        "",
        text,
    )

    return text


def build_financial_context(user):

    wallet = user.wallet

    goals = user.goals.all()

    transactions = wallet.transactions.filter(
        status=TransactionStatus.SUCCESS
    )

    context = {
        "wallet": {
            "available_balance": float(wallet.available_balance),
            "total_funded": float(wallet.total_funded),
            "total_transferred": float(wallet.total_transferred),
            "total_withdrawn": float(wallet.total_withdrawn),
            "total_refunded": float(wallet.total_refunded),
        },

        "goals": [],
        "transactions": [],
        "saving_statistics": {},
    }

    # ==========================
    # GOALS
    # ==========================

    for goal in goals:

        target = goal.target_amount or Decimal("0")
        saved = goal.saved_amount or Decimal("0")

        remaining = max(target - saved, Decimal("0"))

        progress = (
            (saved / target) * 100
            if target > 0
            else Decimal("0")
        )

        context["goals"].append({
            "name": goal.name,
            "description": goal.description,
            "target_amount": float(target),
            "saved_amount": float(saved),
            "remaining_amount": float(remaining),
            "progress_percentage": round(float(progress), 2),
        })

    # ==========================
    # TRANSACTIONS
    # ==========================

    for transaction in transactions:

        context["transactions"].append({
            "transaction_type": transaction.transaction_type,
            "amount": float(transaction.amount),
            "description": transaction.description,
            "created_at": transaction.created_at.isoformat(),
        })

    # ==========================
    # SAVING STATISTICS
    # ==========================

    context["saving_statistics"] = calculate_saving_statistics(
        transactions
    )

    return context




def calculate_saving_statistics(transactions):

    now = timezone.now()

    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    total_deposits = Decimal("0")
    total_transfers = Decimal("0")
    total_withdrawals = Decimal("0")

    weekly_saved = Decimal("0")
    monthly_saved = Decimal("0")

    deposit_count = 0
    transfer_count = 0
    withdrawal_count = 0

    # -------------------------
    # FINANCIAL HISTORY
    # -------------------------

    first_transaction = transactions.order_by(
        "created_at"
    ).first()

    if first_transaction:

        history_start = first_transaction.created_at

        history_days = max(
            (now - history_start).days,
            1
        )

    else:

        history_start = None
        history_days = 0

    # -------------------------
    # TRANSACTIONS
    # -------------------------

    for transaction in transactions:

        amount = transaction.amount

        if transaction.transaction_type == TransactionType.DEPOSIT:

            total_deposits += amount
            deposit_count += 1

        elif transaction.transaction_type == TransactionType.TRANSFER:

            total_transfers += amount
            transfer_count += 1

            if transaction.created_at >= seven_days_ago:
                weekly_saved += amount

            if transaction.created_at >= thirty_days_ago:
                monthly_saved += amount

        elif transaction.transaction_type == TransactionType.WITHDRAWAL:

            total_withdrawals += amount
            withdrawal_count += 1

    # -------------------------
    # AVERAGES
    # -------------------------

    if history_days > 0:

        average_daily_saving = (
            total_transfers / history_days
        )

        average_weekly_saving = (
            average_daily_saving * 7
        )

        average_monthly_saving = (
            average_daily_saving * 30
        )

    else:

        average_daily_saving = Decimal("0")
        average_weekly_saving = Decimal("0")
        average_monthly_saving = Decimal("0")

    # -------------------------
    # HISTORY
    # -------------------------

    history_months = (
        history_days / 30
        if history_days > 0
        else 0
    )

    return {
        "total_deposits": float(total_deposits),
        "total_goal_transfers": float(total_transfers),
        "total_withdrawals": float(total_withdrawals),

        "last_7_days_saved": float(weekly_saved),
        "last_30_days_saved": float(monthly_saved),

        "average_daily_saving": round(
            float(average_daily_saving),
            2
        ),

        "average_weekly_saving": round(
            float(average_weekly_saving),
            2
        ),

        "average_monthly_saving": round(
            float(average_monthly_saving),
            2
        ),

        "history_start": (
            history_start.isoformat()
            if history_start
            else None
        ),

        "history_days": history_days,

        "history_months": round(
            history_months,
            2
        ),

        "deposit_count": deposit_count,
        "goal_transfer_count": transfer_count,
        "withdrawal_count": withdrawal_count,
    }


GENERAL_FINANCIAL = "GENERAL_FINANCIAL"
GOAL_PROJECTION = "GOAL_PROJECTION"
SAVING_RATE = "SAVING_RATE"
GOAL_PRIORITY = "GOAL_PRIORITY"
SAVING_BEHAVIOR = "SAVING_BEHAVIOR"
WALLET = "WALLET"

def detect_financial_intent(question):

    question = question.lower().strip()

    # -------------------------
    # GOAL PROJECTION
    # -------------------------

    projection_patterns = [
        "can i reach",
        "can i achieve",
        "can i hit",
        "will i reach",
        "will i achieve",
        "will i have enough",
        "can i afford",
        "enough by",
        "reach my goal",
        "meet my goal",
        "hit my target",
        "achieve my target",
        "by december",
        "by january",
        "by february",
        "by march",
        "by april",
        "by may",
        "by june",
        "by july",
        "by august",
        "by september",
        "by october",
        "by november",
    ]

    if any(
        pattern in question
        for pattern in projection_patterns
    ):
        return GOAL_PROJECTION

    # -------------------------
    # SAVING RATE
    # -------------------------

    saving_rate_patterns = [
        "how much should i save",
        "how much do i need to save",
        "how much should i put aside",
        "how much do i need",
        "how much per week",
        "how much every week",
        "how much weekly",
        "how much per month",
        "how much monthly",
        "weekly saving",
        "monthly saving",
        "saving rate",
    ]

    if any(
        pattern in question
        for pattern in saving_rate_patterns
    ):
        return SAVING_RATE

    # -------------------------
    # GOAL PRIORITY
    # -------------------------

    priority_patterns = [
        "which goal",
        "what goal",
        "which one should i",
        "what should i prioritize",
        "which should i prioritize",
        "which should i focus on",
        "what should i focus on",
        "which goal should come first",
        "which goal is more important",
        "prioritize my goals",
    ]

    if any(
        pattern in question
        for pattern in priority_patterns
    ):
        return GOAL_PRIORITY

    # -------------------------
    # SAVING BEHAVIOR
    # -------------------------

    behavior_patterns = [
        "why am i behind",
        "why am i falling behind",
        "why am i not saving",
        "why can't i save",
        "why is my saving",
        "am i saving enough",
        "am i doing well",
        "how am i doing",
        "my saving behavior",
        "my saving progress",
        "saving progress",
        "saving less",
        "saving more",
    ]

    if any(
        pattern in question
        for pattern in behavior_patterns
    ):
        return SAVING_BEHAVIOR

    # -------------------------
    # WALLET
    # -------------------------

    wallet_patterns = [
        "wallet balance",
        "wallet",
        "balance",
        "deposit",
        "withdrawal",
        "withdraw",
        "funded",
        "money in my wallet",
    ]

    if any(
        pattern in question
        for pattern in wallet_patterns
    ):
        return WALLET

    # -------------------------
    # FALLBACK
    # -------------------------

    return GENERAL_FINANCIAL



# def select_relevant_financial_context(
#     question,
#     financial_context,
# ):

#     intent = detect_financial_intent(
#         question
#     )

#     context = {}

#     # -------------------------
#     # GOAL PROJECTION
#     # -------------------------

#     if intent == GOAL_PROJECTION:

#         context = {
#             "goals": financial_context["goals"],

#             "saving_statistics": (
#                 financial_context[
#                     "saving_statistics"
#                 ]
#             ),
#         }

#     # -------------------------
#     # SAVING RATE
#     # -------------------------

#     elif intent == SAVING_RATE:

#         context = {
#             "goals": financial_context["goals"],

#             "saving_statistics": (
#                 financial_context[
#                     "saving_statistics"
#                 ]
#             ),
#         }

#     # -------------------------
#     # GOAL PRIORITY
#     # -------------------------

#     elif intent == GOAL_PRIORITY:

#         context = {
#             "goals": financial_context["goals"],

#             "saving_statistics": (
#                 financial_context[
#                     "saving_statistics"
#                 ]
#             ),
#         }

#     # -------------------------
#     # SAVING BEHAVIOR
#     # -------------------------

#     elif intent == SAVING_BEHAVIOR:

#         context = {
#             "goals": financial_context["goals"],

#             "saving_statistics": (
#                 financial_context[
#                     "saving_statistics"
#                 ]
#             ),

#             "recent_transactions": (
#                 financial_context[
#                     "recent_transactions"
#                 ]
#             ),
#         }

#     # -------------------------
#     # WALLET
#     # -------------------------

#     elif intent == WALLET:

#         context = {
#             "wallet": financial_context["wallet"],

#             "recent_transactions": (
#                 financial_context[
#                     "recent_transactions"
#                 ]
#             ),
#         }

#     # -------------------------
#     # GENERAL FALLBACK
#     # -------------------------

#     else:

#         context = {
#             "wallet": financial_context["wallet"],

#             "goals": financial_context["goals"],

#             "saving_statistics": (
#                 financial_context[
#                     "saving_statistics"
#                 ]
#             ),

#             "recent_transactions": (
#                 financial_context[
#                     "recent_transactions"
#                 ]
#             ),
#         }

#     return {
#         "intent": intent,
#         "context": context,
#     }

def select_relevant_financial_context(
    question,
    financial_context,
):

    intent = detect_financial_intent(
        question
    )

    if intent == GOAL_PROJECTION:

        goal = find_goal_from_question(
            question,
            financial_context["goals"],
        )

        # -------------------------
        # No goal specified
        # -------------------------

        if goal is None:

            return {
                "intent": intent,
                "context": None,
                "needs_clarification": True,
                "clarification": (
                    "Which savings goal would "
                    "you like me to check?"
                ),
            }

        # -------------------------
        # Multiple goals matched
        # -------------------------

        if goal == "AMBIGUOUS":

            return {
                "intent": intent,
                "context": None,
                "needs_clarification": True,
                "clarification": (
                    "I found multiple savings goals "
                    "that could match your question. "
                    "Which one would you like me to check?"
                ),
            }

        # -------------------------
        # Specific goal found
        # -------------------------

        return {
            "intent": intent,

            "context": {
                "goal": goal,

                "saving_statistics": (
                    financial_context[
                        "saving_statistics"
                    ]
                ),
            },

            "needs_clarification": False,
            "clarification": None,
        }

    # Other intents continue here...

    

def find_goal_from_question(
    question,
    goals,
):

    question_text = normalize_text(
        question
    )

    matched_goals = []

    for goal in goals:

        goal_name = normalize_text(
            goal["name"]
        )

        # Exact goal name
        if goal_name in question_text:
            matched_goals.append(goal)
            continue

        # Check individual words
        goal_words = goal_name.split()

        matched_words = [
            word
            for word in goal_words
            if len(word) >= 3
            and word in question_text
        ]

        if matched_words:
            matched_goals.append(goal)

    # Exactly one goal matched
    if len(matched_goals) == 1:
        return matched_goals[0]

    # None matched
    if len(matched_goals) == 0:
        return None

    # Multiple goals matched
    return "AMBIGUOUS"