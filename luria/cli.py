import fire
from . import adr_index, collect, concretize, init, link_refs, lint, migrate, new, remotes, reports, site
COMMANDS = {'lint': lint.run, 'link': link_refs.run, 'index': adr_index.run, 'new': new.run, 'concretize': concretize.run, 'migrate': migrate.run, 'remotes': remotes.run, 'site': site.run, 'init': init.run, 'reports': reports.run, 'collect': collect.run}
CI_COMMANDS = {'reports': ('luria.reports', 'write the status reports as markdown'), 'collect': ('luria.collect', 'assemble fragments into their views')}

def main() -> int:
    fire.Fire(COMMANDS, name='luria')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
