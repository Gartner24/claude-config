# Plain words (spec 0028): what the runner tells you, in words you can follow. PLAIN maps every reason code to a
# short phrase and a one or two sentence explanation; jargon() finds the words a report or phone question must not use.
import re

# AC-7: reason -> (words under 60 characters, learn under 300 characters).
PLAIN = {
    "denied": ("a step was refused something it tried to do",
               "The build is kept in a locked room, and it tried to touch a file or run a command outside it. "
               "Allow it if you trust the step, like letting a plumber into one more room; skip to leave it out."),
    "blocked": ("the step needs something only you can do",
                "The build hit a task it cannot do alone, such as typing a password or installing a program. "
                "Do it yourself, then say done so it goes on, or skip this feature for now."),
    "verify_failed": ("the checks found a problem it could not fix",
                      "After building, it tried the feature the way a user would and something did not work. "
                      "Try again gives it another go at the fix; skip leaves the feature for later."),
    "no_progress": ("a step ran but changed nothing",
                    "The step finished without ticking its box or changing any file, like a worker who came and "
                    "left with nothing done. Try again runs it once more; skip moves on."),
    "debug_touched": ("the fix changed tests or plans it should not touch",
                      "While fixing a bug it edited the tests or the written plan, which is like a student changing "
                      "the exam questions. Keep the edits if they look right, or undo them and try again."),
    "unchecked": ("a step said done without its proof line",
                  "Each check must end by saying how many problems it confirmed it would catch. This one did not, "
                  "so nobody knows if it really checked. Try again asks it to redo the step properly."),
    "design_gate": ("the screens did not pass the design review",
                    "Any change to what users see must pass a design review before the feature closes. Try again "
                    "lets it fix the findings; accept as is keeps the screens the way they are."),
    "budget": ("a step hit its spending limit",
               "Each step may spend only so much money on the model. This one used it all before finishing. "
               "Give it more doubles the limit for this feature; skip moves on."),
    "max_calls": ("the feature used all of its tries",
                  "A feature gets a fixed number of model runs so a stuck one cannot run all night. "
                  "Give it more doubles the number; skip moves on to other work."),
    "call_timeout": ("a step ran out of time",
                     "Each step has a time limit, like a parking meter. This one ran past it. Give it more doubles "
                     "the time for this feature; skip moves on."),
    "call_error": ("the model stopped with an error",
                   "The model run ended with an error instead of an answer, often a short outage. "
                   "Retry runs the step again; skip moves on."),
    "manual_box": ("the next step is one you do by hand",
                   "The plan says this step is yours, such as a design choice, so the build does not do it. "
                   "Say done when you did it, or skip it."),
    "waiting": ("the next step is waiting on you",
                "The plan marks this step as yours, for example a check on your phone. Say done when it is done, "
                "or skip it for now."),
    "no_command": ("the next step has no command to run",
                   "Each step in the plan names the command that does it. This one names none, so the build cannot "
                   "tell what to run. Skip the step, or skip the whole feature."),
    "no_feature": ("a step sits outside any feature",
                   "Every step must belong to a feature heading in the plan. This one does not, so the build "
                   "cannot place it. Skip the step, or skip the whole feature."),
    "issue_changed": ("the linked issue changed after the plan was written",
                      "The written plan was made from an issue on GitHub, and someone edited or commented on it since. "
                      "Update the plan first so the build follows the new ask, or go on with the plan as it is."),
    "stack_deep": ("too many unmerged branches are piled up",
                   "Each feature builds on the one before it until that one is merged, like a stack of plates. "
                   "This stack is already three high. Build it off the start instead, or wait for the bottom to merge."),
    "paths_overlap": ("two features running at once touched the same files",
                      "Two features build side by side, each with its own list of files. This one changed a file "
                      "on the other's list. Wait for the other to finish, undo those files, or skip it."),
    "squash_failed": ("the work could not be folded into one save",
                      "Before sharing, the build folds its many small saves into one tidy save. That failed. "
                      "Push the small saves as they are, or skip opening the review request."),
    "private_names": ("a private name showed up in work about to go public",
                      "Before sharing, the build looks for client or work names that must not leave the computer, "
                      "and found one. Look again after fixing it, push anyway if the repo is private, or skip it."),
    "attribution": ("a save credits the model as an author",
                    "A save message names the model as a co-author, which must not be shared. Skip sharing it, or "
                    "push anyway if the message only quotes that pattern as an example."),
    "push_failed": ("the work could not be sent to GitHub",
                    "Sending the branch to GitHub failed, often a login or network problem. Retry sends it again; "
                    "skip leaves the work only on this computer."),
    "base_unpushed": ("the branch it builds on is not on GitHub yet",
                      "This work sits on top of another unshared branch. Push that one too, open the review request "
                      "against the main line instead, or skip it."),
    "pr_failed": ("the review request could not be opened",
                  "The branch reached GitHub, but opening the review request there failed. Retry tries again; "
                  "skip leaves the branch there for you to open by hand."),
    "review_ask": ("a reviewer asked a question on the review request",
                   "Someone left a question on the shared work. Send the suggested reply, let the build change the "
                   "code to answer it, or answer it yourself."),
    "review_never": ("no review ever came",
                     "The review request waited and nobody looked at it, so the build left it for you."),
    "review_rounds": ("the review went back and forth many times",
                      "The reviewer and the build traded fixes five times without finishing. Allow five more rounds, "
                      "or leave the rest to you."),
    "approved": ("the review request was approved",
                 "A reviewer said yes. Merge now joins it to the main line for you, and only your tap does that. "
                 "Later leaves it waiting; I merged it says you already did."),
    "foreign_commits": ("someone else changed files that can run code on this PR",
                        "Another person's commit on your PR changes files that tools load and run, like the model's "
                        "settings or hooks (scripts that run on events) or package scripts. Nothing runs on it until "
                        "you have looked at those commits."),
    "review_request": ("a review was asked of you",
                       "Someone asked you to review their PR (a request to join code). Draft a review lets a model "
                       "read the change as plain text, with no way to run or post anything, and write a draft for you."),
    "review_draft": ("your draft review is ready",
                     "The draft is above. Post as my review publishes it under your name, exactly as shown; edit "
                     "first lets you replace its summary; don't post drops it. Nothing is posted without your tap."),
    "review_edit": ("send the text for your review",
                    "Reply with the summary you want; it replaces the drafted one and you see the draft again."),
    "rebase": ("the branch it builds on moved",
               "The work below this one changed, so this branch must be moved on top of it again and resent. "
               "Do that now, or leave it for you."),
    "rebase_conflict": ("moving the branch hit clashing edits",
                        "Moving this work on top of the newer work found the same lines changed both ways. Leave it "
                        "for you to sort out, or try again."),
    "app_failed": ("the app would not start for the checks",
                   "To check the feature it starts your app, like turning a machine on before testing it. "
                   "The app did not come up. Retry starts it again; skip moves on."),
    "branch": ("the work needed its own branch",
               "A branch is a separate copy of the code where work happens before it joins the main line. "
               "The build made one for this work."),
    "branch_changed": ("the code was switched to another branch",
                       "Someone moved the folder to a different copy of the code during the build. Go on builds on "
                       "the new one, switch back returns to the old one, or stop this repo."),
    "scope_unreadable": ("the plan file could not be read",
                         "The build reads its to do list from the plan file, and that file is missing or broken. "
                         "Retry reads it again after you fix it; or stop this repo."),
    "autopilot_off": ("you turned the night build off for this repo",
                      "The plan file says this repo may no longer build on its own, so the build left it."),
    "interrupted": ("you stopped the build",
                    "The build was stopped from the keyboard or by the computer, so it ended where it was."),
    "run_limit": ("the build reached its hour limit",
                  "A build may run only so many hours, like a shift. Keep going adds another shift; stop ends it."),
    "usage_limit": ("the model usage limit was reached",
                    "Your plan allows only so much model use per few hours. The build sleeps until it resets, then "
                    "goes on."),
    "api_outage": ("the model service was down",
                   "The model service was not answering, like a phone line that is down. Keep waiting gives it "
                   "more time; or stop this repo."),
    "guard_changed": ("the setup changed during the build",
                      "Settings or safety files the build relies on changed while it ran. Accept the new setup if "
                      "you made the change; or stop this repo to be safe."),
    "crash_loop": ("two features failed the same way in a row",
                   "When two features fail with the same error one after the other, something bigger is wrong, "
                   "like two lamps going dark at once. Retry tries again; or stop this repo."),
    "app_port_busy": ("another program holds the app's address",
                      "The app needs a fixed address on this computer, like a parking spot, and another program "
                      "is using it. Close that program and retry, or stop this repo."),
    "spawn_failed": ("the model program would not start",
                     "The build could not start the model program at all, often after an update. Retry tries "
                     "again; or stop this repo."),
    "ping_failed": ("a phone message could not be sent",
                    "The build could not reach your phone. It keeps building and sends the message again later."),
    "internal_error": ("the build tool itself hit a bug",
                       "Not your code: the build tool broke. It stopped this repo and saved the error details for "
                       "a fix."),
    "auto_off": ("you turned autonomous mode off",
                 "You typed /auto off, so the build finished the features it had started and took no new ones."),
    "queue_done": ("all queued work is done",
                   "The build went through every feature it was allowed to build."),
    "decision_open": ("it is waiting for your answer",
                      "The build asked you a question and moved on to other work until you answer."),
    "feature_done": ("the feature was built",
                     "Every step of the feature passed, and it is ready for you to review and merge."),
}

# AC-7: a word may be added, never removed without a spec.
WORDS = ("park", "parked", "traceback", "stderr", "stdout", "sigint", "sigterm", "flock", "session id", "exit code",
         "repo stop", "run stop", "guard", "cap", "budget", "fingerprint", "sandbox", "deny list", "allow list",
         "scrub", "ntfy")
SNAKE = re.compile(r"\b[a-z]+_[a-z0-9_]+\b")
CODES = re.compile(r"\bAC-\d+\b|\bspec \d{4}\b", re.I)
WORD = re.compile(r"\b(" + "|".join(re.escape(w) for w in WORDS) + r")\b", re.I)


def jargon(text):
    """AC-7: the sorted distinct jargon hits in text; tokens holding a / (paths, URLs) are left out."""
    text = " ".join(t for t in str(text).split() if "/" not in t)
    hits = set(SNAKE.findall(text)) | set(CODES.findall(text)) | {m.casefold() for m in WORD.findall(text)}
    return sorted(hits)


def words(reason):
    """The plain phrase for a reason code; an unknown code stays as it is."""
    return PLAIN.get(reason, (reason,))[0]


def detail(text):
    """A detail in plain form: every reason code in it read as its plain words."""
    return SNAKE.sub(lambda m: words(m.group(0)), str(text))
