from time import sleep

from celery import shared_task

from .models import Problem, Solution


@shared_task
def check_answer_and_update_score(problem_id, solution_id):
    """call after solution model saved"""
    # TODO : atomic?

    # TODO : how to notify to client when this task finished
    # web-socket, receive callback url from client,

    # update state
    solution = Solution.objects.get(pk=solution_id)
    solution.state = Solution.CHEKING
    solution.save()

    sleep(20)  # condition.

    problem = Problem.objects.get(pk=problem_id)

    # compare answer with given answer
    score = 100 if solution.answer == problem.answer.answer else 0
    solution.score = score
    solution.state = Solution.CHECK_DONE
    solution.save()

    # update submission
    if score == 100:
        submission = solution.submission
        submission.score = max(submission.score, score)
        submission.save()

    return score
