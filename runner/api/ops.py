import datetime
import logging
logger = logging.getLogger(__name__)

from connexion import NoContent
import runner_db as db

STATUS={
    'OK': 200,
    'CREATED': 201,
    'ACCEPTED': 203,
    'NO_CONTENT': 204,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404
}

def get(op_id):
    op=db.get_op(int(op_id))
    if op:
        return op, STATUS['OK']
    else:
        return NoContent, STATUS['NOT_FOUND']

# TODO:  Get all ops by unit name, ordered by datetime field
# def search(limit=10, unit='default', latest=True):
#     try:
#         return db.get_ops_by_unit(name)[0:limit], STATUS['OK']
#     except NameError:
#         return db.get_ops()[0:limit], STATUS['OK']
