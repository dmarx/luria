from __future__ import annotations
import os
CI_VARS = ('CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'CIRCLECI', 'BUILDKITE', 'TF_BUILD', 'TEAMCITY_VERSION', 'JENKINS_URL')
FALSEY = {'', '0', 'false', 'no', 'off'}

def running_in_ci(env: dict[str, str] | None=None) -> bool:
    env = os.environ if env is None else env
    return any((env.get(v, '').strip().lower() not in FALSEY for v in CI_VARS))

def regenerate_remedy(command: str='luria index') -> str:
    if not running_in_ci():
        return f'run `{command}`'
    return f'regenerate and commit the result — run `{command}` locally, or give CI a generation job that runs it and pushes what it wrote. Adding `{command}` to this checking job is not enough on its own: nothing would commit its output, and this check would be comparing that output against itself'
