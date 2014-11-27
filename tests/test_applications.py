import json
from click.testing import CliRunner
from mock import MagicMock
import yaml
from aws_minion.cli import cli
from aws_minion.context import Context, ApplicationNotFound, Application


def raise_application_not_found(x):
    raise ApplicationNotFound('blub')

def test_create_application(monkeypatch):
    monkeypatch.setattr('boto.ec2.connect_to_region', MagicMock())
    monkeypatch.setattr('boto.iam.connect_to_region', MagicMock())
    monkeypatch.setattr('time.sleep', lambda s: s)

    context = Context({'region': 'caprica', 'vpc': 'myvpc'})
    context.get_application = raise_application_not_found
    context_constructor = lambda x: context

    monkeypatch.setattr('aws_minion.cli.Context', context_constructor)

    runner = CliRunner()

    data = {
        'application_name': 'myapp',
        'team_name': 'MyTeam',
        'exposed_ports': [123]
    }

    with runner.isolated_filesystem():
        with open('myapp.yaml', 'w') as fd:
            yaml.dump(data, fd)

        with open('config.yaml', 'w') as fd:
            yaml.dump(context.config, fd)

        result = runner.invoke(cli, ['--config-file', 'config.yaml', 'applications', 'create', 'myapp.yaml'], catch_exceptions=False)

    assert 'Creating IAM role and instance profile.. OK' in result.output


def test_list_applications(monkeypatch):
    context = Context({'region': 'caprica', 'vpc': 'myvpc'})

    security_group = MagicMock()
    security_group.tags = {'Manifest': yaml.dump({'application_name': 'myapp', 'team_name': 'MyTeam', 'exposed_ports': [123]})}

    context.get_applications = lambda: [Application('myapp', security_group)]
    context_constructor = lambda x: context

    monkeypatch.setattr('aws_minion.cli.Context', context_constructor)

    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('config.yaml', 'w') as fd:
            yaml.dump(context.config, fd)

        result = runner.invoke(cli, ['--config-file', 'config.yaml', 'app'], catch_exceptions=False)

    lines = result.output.splitlines()
    assert lines[1].split() == ['myapp', 'MyTeam', '[123]']
