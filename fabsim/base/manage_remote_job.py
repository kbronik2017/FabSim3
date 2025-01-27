
import sys
import time
from typing import Optional

from beartype import beartype

from fabsim.base.decorators import task
from fabsim.base.env import env
from fabsim.base.networks import local, run
from fabsim.deploy.templates import template


@task
def stat() -> None:
    '''
    Check the remote message queue status for individual machines.
    Syntax: fab <machine> stat.

    TODO: Respect varying remote machine queue systems.
    '''
    check_jobs_dispatched_on_remote_machine()
    jobsInfo = jobs_list(quiet=True)
    # jobs_list(quiet=True)
    print(jobsInfo)


@beartype
def jobs_list(quiet: Optional[bool] = False) -> str:
    """
        options:
                quiet = True : hide the command output
    """
    CRED = '\33[31m'
    CEND = '\33[0m'
    if (
            hasattr(env, 'dispatch_jobs_on_localhost') and
            isinstance(env.dispatch_jobs_on_localhost, bool) and
            env.dispatch_jobs_on_localhost
    ):

        # output = local(template("$stat "), capture=quiet).splitlines()
        output = run(template("$stat "), capture=quiet)
        return output

    elif env.manual_sshpass:
        pre_cmd = "sshpass -p '%(sshpass)s' ssh %(username)s@%(remote)s " % env
        manual_command = template("$stat")
        # manual_command = '"' + manual_command + '"'
        print('manual_command', manual_command)
        output = local(pre_cmd + "'" + manual_command + "'", capture=False)
        string = CRED + 'The stat of your submitted job is shown' \
                        ' in the table above!' + CEND
        return string
        # print('output', output)
        # output = local(
        #     template(
        #         pre_cmd +
        #         manual_command
        #     )
        # )
        # output = local(pre_cmd + str(manual_command) , capture=False)

    else:

        output = run(template("$stat"), capture=quiet)
        return output

    # return output


@task
@beartype
def cancel_job(jobID: Optional[str] = None) -> None:
    """
        Cancel a remote job.
        Syntax: fab <machine> cancel_job:jobID

        note : if the jobID is empty, this function cancel all submitted
               job which are not in FINISHED status
    """

    check_jobs_dispatched_on_remote_machine()

    if jobID is None:
        print("ERROR: No jobID is passed,\n\tusage Syntax :"
              "\n\t\tfab <machine> cancel_job:jobID= <input_jobID>")
        sys.exit()

    env.jobID = jobID

    if (
            hasattr(env, "dispatch_jobs_on_localhost") and
            isinstance(env.dispatch_jobs_on_localhost, bool) and
            env.dispatch_jobs_on_localhost
    ):
        local(template(template.template("$cancel_job_command")))
    elif env.manual_sshpass:
        pre_cmd = "sshpass -p '%(sshpass)s' ssh %(username)s@%(remote)s " % env
        manual_command = template("$cancel_job_command $jobID")
        local(pre_cmd + "'" + manual_command + "'", capture=False)

    else:
        run(template(template("$cancel_job_command")))


def check_jobs_dispatched_on_remote_machine() -> None:
    if env.remote == "localhost":
        print("ERROR: This functionality can be used only when"
              "jobs are submitted on the remote machine")
        sys.exit()


@beartype
def check_complete(jobname_syntax: Optional[str] = "") -> bool:
    """
    Return true if the user has no job running containing
    jobname_syntax in their name
    """
    time.sleep(10)

    check_jobs_dispatched_on_remote_machine()
    jobs_dict = jobs_list(quiet=True)

    if len(jobs_dict) > 0:
        print("The number of active (not finished) jobs = {}".format(
            len(jobs_dict))
        )
        return False
    else:
        print("All jobs are finished :)")
        return True


@task
def wait_complete(jobname_syntax: str = "") -> None:
    """
    Wait until jobs currently running containing jobname_syntax in
    their name are complete, then return
    """
    # time.sleep(120)
    while not check_complete(jobname_syntax):
        time.sleep(110)
