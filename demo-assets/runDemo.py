#!/usr/bin/env python3
import os
import logging
import requests
import re
from subprocess import call,run
import user_info, config_changer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('runDemo')
base_url = None
auth    = None
headers = None
settings = None
configHelper = config_changer.ConfigChanger()

"""
This is the primary flow of demo
"""
def main():
    loadConfiguration()
    get_gh_user()

    #reset state
    force_latest_on_main()
    happy_branch = f'demo-{settings.username}'
    sync_or_create_branch(happy_branch)
    logger.info('\n\tReady on My Demo Branch %s!!\n',happy_branch)
   
    #Add config violation & pause
    input("Hit enter to push policy failure")
    commit_policy_failure()
    push_changes(happy_branch)
   
    #Add Config violation fix, spawn pass and fail branches & pause
    input("Hit enter to FIX policy failure, and spawn test failures and pass")
    remove_policy_failure()
    push_changes(happy_branch)

    # TODO: failed tests too
    #fail_branch = f'demo-{settings.username}-fails'
   # sync_or_create_branch(fail_branch)
   # commit_bad_tests()
   # push_changes(fail_branch)






def loadConfiguration():
    global auth,headers, settings, configHelper
    configHelper.load_config('.circleci/config.yml')
    settings = user_info.UserInfo.from_file()
    auth=(settings.username,settings.github_token)
    headers={"Authorization":f'Bearer {settings.github_token}',"X-GitHub-Api-Version":"2022-11-28"}
    base_url=f'https://api.github.com/repos/{settings.orgname}/{settings.reponame}'
    logger.info("using base URL: " + base_url )

def get_gh_user():
    r = requests.get("https://api.github.com/user",auth=auth)
    if r.status_code == 200:
        logger.info('\t\tLet\'s do this demo %s!!\n',r.json()['name'])
    else:
        logger.error(f'GH check failed with response code: {r.status_code}')
        logger.error(r.text)
        exit(1)

def force_latest_on_main():
    cur_branch = run(['git','branch','--show-current'], capture_output=True)
    if cur_branch.stdout != 'main':
        logger.info("\tNot on main,switching..")
        output = run(['git','stash','push'],capture_output=True)
        output = run(['git','checkout','main'],capture_output=True)
    logger.info("\tPulling latest changes into main..")
    run(['git','pull'],capture_output=True)
    logger.info('\tReady on Main\n')


def sync_or_create_branch(name):
    run(['git','branch','-D',name],capture_output=True)
    run(['git','checkout', '-b',name],capture_output=True)
    logger.debug("\tNew branch %s created",name)
    logger.debug(f'Ensuring {name} has latest from main..')
    run(['git','reset','--hard', 'main'],capture_output=True)
    logger.info("\t%s ready",name)


def commit_policy_failure():
    configHelper.add_policy_violation()
    run(['git','add','.circleci/config.yml'],capture_output=True)
    run(['git','commit', '-m',"Violate config policy with prod contex on non default branch"],capture_output=True)

def remove_policy_failure():
    configHelper.remove_policy_violation()
    run(['git','add','.circleci/config.yml'],capture_output=True)
    run(['git','commit', '-m',"Remove policy violation"],capture_output=True)

def push_changes(branch_name):
    run(['git','push','-f','--set-upstream','origin',branch_name ], capture_output=True)
    logger.info("Changes pushed")


def commit_bad_tests():
    run(["touch","example.file"],capture_output=True)
    run(['git','add','example.file'],capture_output=True)
    run(['git','commit', '-m',"Dev work with failing tests.."],capture_output=True)



main()
