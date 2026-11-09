from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('api/graphql.md', 'docs/platform/public-graphql-m2m-v1.md')
FLAGS = ('listen', 'server-name', 'server-cert', 'server-key', 'allowed-assets')
QUERIES = ('semanticPVCurrent', 'semanticStorageCurrent', 'semanticEVSECurrent')


def matches(page, handler, config, binder, runtime):
    required = ('| `/graphql/m2m/v1` | Implemented, default off |',
                '| `m2mCurrentSnapshot` | Unimplemented target |',
                '| Partial gateway settings | Rejected |')
    disabled = re.search(r'func \(config M2MGraphQLConfig\) Disabled\(\) bool \{(.*?)\n}', config, re.S)
    validate = re.search(r'func \(config M2MGraphQLConfig\) Validate\(\) error \{(.*?)\n}', config, re.S)
    return (all(row in page for row in required)
            and all(q in page and q in handler for q in QUERIES)
            and 'route                     = "/graphql/m2m/v1"' in handler
            and '"/graphql/m2m/v1"' in runtime
            and all('m2m-graphql-' + flag in page and '"m2m-graphql-' + flag + '"' in binder for flag in FLAGS)
            and 'm2m-graphql-enabled' not in page and '"m2m-graphql-enabled"' not in binder
            and disabled is not None and all(x in disabled.group(1) for x in ('ListenAddr == ""', 'ServerName == ""', 'ServerCertFile == ""', 'ServerKeyFile == ""', 'len(config.AllowedAssets) == 0'))
            and validate is not None and all(x in validate.group(1) for x in ('configuration is incomplete', 'empty allowed asset', 'duplicate allowed asset')))


# Self-contained excerpts of the gateway facts the pages must match, so the
# test does not depend on any provisioned external checkout.
HANDLER = '''route                     = "/graphql/m2m/v1"
semanticPVCurrent semanticStorageCurrent semanticEVSECurrent'''
CONFIG = '''func (config M2MGraphQLConfig) Disabled() bool {
	return config.ListenAddr == "" && config.ServerName == "" && config.ServerCertFile == "" &&
		config.ServerKeyFile == "" && len(config.AllowedAssets) == 0
}

func (config M2MGraphQLConfig) Validate() error {
	// configuration is incomplete / empty allowed asset / duplicate allowed asset
	return errors.New("configuration is incomplete: empty allowed asset or duplicate allowed asset")
}
'''
BINDER = '\n'.join('"m2m-graphql-' + flag + '"' for flag in FLAGS)
RUNTIME = '"/graphql/m2m/v1"'


def test_status_against_gateway_facts():
    handler, config, binder, runtime = HANDLER, CONFIG, BINDER, RUNTIME
    for path in PAGES:
        page = (ROOT / path).read_text()
        assert matches(page, handler, config, binder, runtime)
        for bad in (page.replace('| `/graphql/m2m/v1` | Implemented, default off |', '| `/wrong` | Implemented, default off |'),
                    page + '\nm2m-graphql-enabled',
                    page.replace('| Partial gateway settings | Rejected |', '| Partial gateway settings | Accepted |'),
                    page.replace('| `m2mCurrentSnapshot` | Unimplemented target |', '| `m2mCurrentSnapshot` | Implemented |')):
            assert not matches(bad, handler, config, binder, runtime)
