import boto3
import botocore
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def filter_instances(project,force):
    instances = []

    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    elif force:
        instances = ec2.instances.all()
    else:
        print('There is no project option set for this command')
        exit()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
def cli():
    """Shotty manages snapshots"""

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
    help="Only volumes for project (tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all snapshots, not just the ones recently completed")
@click.option('--force', 'force', default=True, is_flag=True,
    help="Force the command if project not set")

def list_snapshots(project, list_all,force):
    "List EC2 snapshots"
    instances = filter_instances(project,force)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(', '.join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
            )))

            if s.state == 'completed' and not list_all: break
    return

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None,
    help="Only volumes for project (tag Project:<name>)")
@click.option('--force', 'force', default=True, is_flag=True,
    help="Force the command if project not set")

def list_volumes(project,force):
    "List EC2 volumes"
    instances = filter_instances(project,force)

    for i in instances:
        for v in i.volumes.all():
            print(', '.join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GB",
                v.encrypted and "Encripted" or "Not Encrypted"
            )))
    return

@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('snapshots', help="Create snapshots for all volumes")
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
@click.option('--force', 'force', default=False, is_flag=True,
    help="Force the command if project not set")

def create_snapshots(project,force):
    "Create snapshots for EC2 instances"
    instances = filter_instances(project,force)

    for i in instances:
        print("Stopping {0} ... ".format(i.id))

        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("Skipping {0}, snapshot already in progress ".format(v.id))
                continue

            print("  Creating snapshot for {0}".format(v.id))
            v.create_snapshot(Description="Created by SnapshotAlyer 30000")

        print("Starting {0} ...".format(i.id))

        i.start()
        i.wait_until_running

    print("Job Done!!!")
    return

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
@click.option('--force', 'force', default=True, is_flag=True,
    help="Force the command if project not set")

def list_instances(project,force):
    "List EC2 Instances"
    instances = filter_instances(project,force)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or []}
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
            )))
    return

@instances.command('reboot')
@click.option('--project', default=None,
    help="Only instances for project")
@click.option('--force', 'force', default=False, is_flag=True,
    help="Force the command if project not set")

def reboot_instances(project,force):
    "Reboot EC2 Instances"
    instances = filter_instances(project,force)

    for i in instances:
        print("Rebooting {0} ... ".format(i.id))
        try:
            i.reboot()
        except botocore.exceptions.ClientError as e:
            print("Could not reboot {0} ".format(i.id) + str(e))
            continue

    return

@instances.command('stop')
@click.option('--project', default=None,
    help="Only instances for project")
@click.option('--force', 'force', default=False, is_flag=True,
    help="Force the command if project not set")

def stop_instances(project,force):
    "Stop EC2 Instances"
    instances = filter_instances(project,force)

    for i in instances:
        print("Stopping {0} ...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Could not stop {0} ".format(i.id) + str(e))
            continue

    return

@instances.command('start')
@click.option('--project', default=None,
    help="Only instances for project")
@click.option('--force', 'force', default=False, is_flag=True,
    help="Force the command if project not set")

def start_instances(project,force):
    "Start EC2 Instances"
    instances = filter_instances(project,force)

    for i in instances:
        print("Starting {0} ...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Could not start {0} ".format(i.id) + str(e))
            continue

    return

if __name__ == '__main__':
    cli()
