
import datetime
import logging
logger = logging.getLogger(__name__)

from connexion import NoContent
import runner_db as db
import runner

STATUS={
    'OK': 200,
    'CREATED': 201,
    'ACCEPTED': 203,
    'NO_CONTENT': 204,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404
}

def post(**kwargs):
    unit_id=kwargs['unit_id']
    action=kwargs['action']
    unit=db.get_unit(unit_id)
    if unit:
        if unit['data_dir']:
            logger.debug("Configuring unit #%s action: %s", unit['unit_id'], action)
            op = db.create_op_in_unit(unit_id, { 'action': action })
            logger.debug("Unit #%s Op: %s", unit['unit_id'], str(op))
            task = runner.Runner(
                op_id = op['op_id'], 
                data_dir = unit['data_dir'], 
                project_dir = unit['name'], 
                # run_handler = lambda event: db.update_op(event, ephemeral=True),
                done_handler = lambda event: db.update_op(event, ephemeral=False) )
            logger.info("Unit #%s Starting action: %s", unit['unit_id'], action)
            task.start(unit['name'], action)
            #^ TODO: catch ValueError('private_data_dir path is either invalid or does not exist')
            return str(task), STATUS['CREATED']
        else:
            return unit or NoContent, STATUS['FORBIDDEN']
    else:
        return unit or NoContent, STATUS['NOT_FOUND']

def delete(unit_id):
    unit_id = int(unit_id)
    logger.warning("Not Implemented!")
    if db.get_unit(unit_id) is None:
        return NoContent, STATUS['NOT_FOUND']
    return NoContent, STATUS['NO_CONTENT']

def put(body, **kwargs):
    logger.debug("PUT Unit #%s: %s", kwargs['unit_id'], str(body))
    unit_id=kwargs['unit_id']

    data_dir=body.get('data_dir')
    unit=db.get_unit(unit_id)
    if unit:
        body.update({ 'name': unit['name'] })

        newunit = unit.update(body)
        logger.debug("New Unit %s: %s", str(newunit), str(body) )

        return db.update_unit(unit), STATUS['OK']
    else:
        return NoContent, STATUS['NOT_FOUND']

def get(unit_id):
    unit_id = int(unit_id)
    unit = db.get_unit(unit_id)
    if unit:
        return unit, STATUS['OK']
    else:
        return NoContent, STATUS['NOT_FOUND']

def search(limit=100, tag='default', latest=False):
    try:
        return db.get_units_by_tag(tag)[0:limit], STATUS['OK']
    except NameError:
        return db.get_units()[0:limit], STATUS['OK']
