import datetime

from connexion import NoContent
import runner_db as db

STATUS={
    'OK': 200,
    'CREATED': 201,
    'ACCEPTED': 203,
    'NO_CONTENT': 204,
    'NOT_FOUND': 404
}

def post(body, **kwargs):
    units_list = body.get('units')
    tag = (body.get('tag') or kwargs['tag'])
    if units_list:
        job = db.create_job(tag or 'default')
        units = [ db.create_unit_in_job(x, job['job_id']) 
                     for x in units_list ]
        job['units'] = units
        return job, STATUS['CREATED']
    else:
        return db.create_job(tag or 'default'), STATUS['CREATED']

def put(body, **kwargs):
    units_list = body.get('units')
    tag = body.get('tag')
    status = None
    job = db.get_job(kwargs['job_id'])
    if units_list:
        new_units = None
        if job.get('units'):
            new_units = set(units_list).difference(
                [ x['name'] for x in job['units'] ] )
            if new_units:
                job['units'] = [ 
                    db.create_unit_in_job(
                        x, kwargs['job_id']) 
                    for x in new_units ]
                status=STATUS['CREATED']
        else:        
            job['units'] = [ 
                db.create_unit_in_job(
                    x, kwargs['job_id']) 
                for x in units_list ]
            status = STATUS['OK']
    if tag:
        if job['tag'] == tag:
            status = status or STATUS['NO_CONTENT']
        else:
            db.update_job(tag=tag)
            job['tag'] = tag
            status = status or STATUS['OK']
    return job, status or STATUS['NO_CONTENT']

def delete(job_id):
    job_id = int(job_id)
    job = db.get_job(job_id)
    if job is None:
        return NoContent, STATUS['NOT_FOUND']
    else:
        db.delete_job(job_id)
        return NoContent, STATUS['NO_CONTENT']

def get(job_id, **kwargs):
    job_id = int(job_id)
    job = db.get_job(job_id)
    if job:
        return job, STATUS['OK']
    else:
        return NoContent, STATUS['NOT_FOUND']

def search(limit=100, tag=None, latest=False):
    if tag:
        if latest:
            return db.get_latest_job_by_tag(tag), STATUS['OK']
        else:
            return db.get_jobs_by_tag(tag)[0:limit], STATUS['OK']
    else:
        if latest:
            return db.get_latest_job(), STATUS['OK']
        else:
            return db.get_jobs(), STATUS['OK']
