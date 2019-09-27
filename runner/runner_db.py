#!/usr/bin/python3
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
import json
import datetime
import os

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)

db_file=os.environ.get('RUNNER_DB') or '/tmp/runner.db'
time_fmt='%Y-%m-%d %H:%M:%S'

db = SqliteDatabase(db_file)

class Job(Model):
    class Meta:
        database = db
        table_name = 'job'

    job_id = PrimaryKeyField()
    tag = CharField()
    created = DateTimeField([time_fmt], default=datetime.datetime.now())

    def from_json(cls, json_data):
        logger.debug(str(help(cls)))
        return Job.update(
            tag=json_data['tag']
        )

    def to_json(self):
        return (json.dumps(model_to_dict(self), indent=2, sort_keys=True, default=str))

    def serialize(self):
        return {
            'job_id': self.job_id,
            'tag': self.tag,
            'created': self.created,
            'units': get_units_in_job(self.job_id)
        }

    def __repr__(self):
        return self.to_json()


class Unit(Model):
    class Meta:
        database = db
        table_name = 'unit'

    job = ForeignKeyField(Job, backref='units', on_delete='CASCADE')
    unit_id = PrimaryKeyField()
    data_dir = CharField(default='')
    name = CharField()

    def from_json(self, json_data):
        logger.debug("Updating Unit %s with data: %s", str(self), str(json_data))
        self.data_dir = json_data.get('data_dir') or self.data_dir
        self.name = json_data.get('name') or self.name
        return self.save()

    def to_json(self):
        return (json.dumps(model_to_dict(self), indent=2, sort_keys=True, default=str))

    def serialize(self):
        return {
            'unit_id': self.unit_id,
            'data_dir': self.data_dir,
            'name': self.name,
            'ops': get_ops_in_unit(self.unit_id)
        }

    def __repr__(self):
        return self.to_json()


class Op(Model):
    class Meta:
        database = db
        table_name = 'op'

    unit = ForeignKeyField(Unit, backref='ops', on_delete='CASCADE')
    op_id = PrimaryKeyField()
    action = CharField()
    task = CharField(default='')
    status = CharField(default='new')

    def from_json(self, json_data, **kwargs):
        ephemeral = kwargs.get('ephemeral') or False
        status = json_data.get('status') or self.status
        stdout = json_data.get('stdout')

        assert int(str(self)) == json_data.pop('op_id')
        if stdout and not ephemeral:
            add_stdout_to_op(self.op_id, json_data.pop('stdout'))
        self.action = json_data.get('action') or self.action
        self.task = json_data.get('task') or ''
        self.status = json_data.get('status') or self.status

        logger.debug("Updating Op (%s) from JSON with data: %s", str(self), str(json_data))

        return self.save()

    def to_json(self):
        return (json.dumps(model_to_dict(self), indent=2, sort_keys=True, default=str))

    def serialize(self):
        return {
            'op_id': self.op_id,
            'action': self.action,
            'task': self.task,
            'status': self.status,
            'stdout': ''.join(get_stdout_in_op(self.op_id))
        }

    def serialize_summary(self):
        return {
            'op_id': self.op_id,
            'action': self.action,
            'status': self.status
            # 'stdout_length': len(get_stdout_in_op(self.op_id))) # todo: db f(n)
        }

    def __repr__(self):
        return self.to_json()

class StdOut(Model):
    class Meta:
        database = db
        table_name = 'stdout'

    op = ForeignKeyField(Op, backref='stdout', on_delete='CASCADE')
    lines = TextField(default='')

    def to_json(self):
        return (json.dumps(model_to_dict(self), indent=2, sort_keys=True, default=str))

    def serialize(self):
        return str(self.lines)

    def __repr__(self):
        return self.to_json()

# TODO docs like this everywhere?
def create_job(tag='default', status='started'):
    """
    Create a new job
    :param job: { tag, status }
    :return: Job ORM object
    """
    return Job.create(tag=tag).serialize()

def get_jobs():
    return [ x.serialize() for x in Job.select().order_by(Job.job_id.asc()).execute().iterator() ]

def get_job(job_id):
    try:
        return Job.select().where(Job.job_id == job_id).get().serialize()
    except DoesNotExist:
        return None 

def update_job(**kwargs):
    job_id=kwargs['job_id']
    try:
        job = Job.select().where(Job.job_id == job_id).get()
    except DoesNotExist:
        return None 
    if 'tag' in kwargs.keys():
        tag = kwargs.get('tag') 
        job.update( tag=tag )
    if 'units' in kwargs.keys():
        units = kwargs.get('units') or job.units
        job.update( units=units)
    return job.serialize()


def get_latest_job():
    try:
        return Job.select().order_by(Job.job_id.desc()).get().serialize()
    except DoesNotExist:
        return None 

def get_jobs_by_tag(tag):
    return [ x.serialize() for x in Job.select().order_by(Job.job_id.desc()).where(Job.tag.in_([tag])).execute().iterator() ]

def get_latest_job_by_tag(tag):
    try:
        return Job.select().where(Job.tag.in_([tag])).order_by(Job.job_id.desc()).get().serialize()
    except DoesNotExist:
        return None 

def create_unit_in_job(name, job_id):
    return Unit.create( name=name, job=job_id).serialize()

def create_unit_in_latest_job_by_tag(name, job_tag):
    return Unit.create( name=name, job=get_latest_job_by_tag(job_tag).job_id).serialize()

def get_unit(unit_id):
    try:
        return (Unit
                .select()
                .where(Unit.unit_id == unit_id)
                .get().serialize())
    except DoesNotExist:
        return None 

def get_units_by_tag(tag):
    return [ x.serialize() for x in 
             ( Unit
               .select()
               .join(Job)
               .where(Job.tag.in_([tag]))
               .execute().iterator() ) ]

def get_units_in_job(job_id):
    return [ x.serialize() for x in 
             ( Unit
               .select()
               .join(Job)
               .where(Job.job_id == job_id)
               .execute().iterator() ) ]

def get_units_in_latest_job():
    return [ x.serialize() for x in 
             ( Unit
               .select()
               .join(Job)
               .where(Job.job_id == get_latest_job().job_id)
               .execute().iterator() ) ]

def get_units_in_latest_job_by_tag(tag):
    return [ x.serialize() for x in (Unit
            .select()
            .join(Job)
            .where(Job.job_id == get_latest_job_by_tag(tag).job_id)
            .execute().iterator()) ]

def get_todays_jobs():
    return [ x.serialize() for x in (Job
            .select()
            .where(
                Job.created >= datetime.date.today()
            ).execute().iterator()) ]

#test me, if needed
def get_todays_jobs_by_tag(tag):
    return [ x.serialize() for x in (Job
            .select()
            .where(
                Job.created >= datetime.date.today() &
                Job.tag == tag
            ).execute().iterator()) ]

def delete_job(job_id):
    try:
        return Job.select().where(Job.job_id == job_id).get().delete_instance(recursive=True)
    except DoesNotExist:
        return None 

def update_unit(json_spec):
    logger.debug("Updating Unit %s: %s", json_spec['unit_id'], str(json_spec))
    return ( Unit
             .select()
             .where(Unit.unit_id == json_spec['unit_id'])
             .get().from_json(json_spec))


def create_op_in_unit(unit_id, json_spec):
    return Op.create( action=json_spec['action'], unit=unit_id).serialize()


def update_op(json_spec, **kwargs):
    logger.debug("Updating Op %s (%s): %s", json_spec['op_id'], str(kwargs or {}), str(json_spec))
    return ( Op
             .select()
             .where(Op.op_id == json_spec['op_id'])
             .get().from_json(json_spec, ephemeral=kwargs.get('ephemeral')) )

def get_units_in_job(job_id):
    return [ x.serialize() for x in 
             ( Unit
               .select()
               .join(Job)
               .where(Job.job_id == job_id)
               .execute().iterator() ) ]

def get_op(op_id):
    try:
        return (Op
                .select()
                .where(Op.op_id == op_id)
                .get().serialize())
    except DoesNotExist:
        return None 

def get_ops_in_unit(unit_id):
    return [ x.serialize_summary() for x in 
             ( Op
               .select()
               .join(Unit)
               .where(Unit.unit_id == unit_id)
               .execute().iterator() ) ]

def get_stdout_in_op(op_id):
    return [ x.serialize() for x in 
             ( StdOut
               .select()
               .join(Op)
               .where(Op.op_id == op_id)
               .execute().iterator() ) ]

def add_stdout_to_op(op_id, stdout):
    logger.debug("ADDING STDOUT to Op %s Output: %s", op_id, stdout)
    return StdOut.create( lines=stdout, op=op_id ).serialize()


def init():
    db.connect()
    db.create_tables([Job, Unit, Op, StdOut])

def main():
    logger.info("%s", str(get_jobs()))

init()
if __name__ == '__main__':
    main()
