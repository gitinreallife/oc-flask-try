from app.api import api_bp
from flask import jsonify, request, url_for, abort
from datetime import datetime
from app import db, socketio
# , socketio
from app.models import ResourceUsage, Resource, ResourceUsageSchema
# from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from sqlalchemy import cast, Date, func
from flask_socketio import emit, send


# get on frontend to see how it works index.html
# @socketio.on('rt-resource-usage')
@socketio.on('get-rt-usage')
def get_rt_usage(param=None):
    query = get_rt_resource_usage()
    resource_usage_schema = ResourceUsageSchema(many=True)
    data = resource_usage_schema.dump(query)

    res = {
        "_count": query.count(),
        "data": data  # ["items"]
    }
    emit('listen-rt-usage', res, broadcast=True)


def get_rt_resource_usage(param=None):
    if param is None:
        param = {
            'resource_name': '',
            'usage_type_code': ''
        }
    subquery = db.session.query(
        ResourceUsage,
        func.rank().over(
            order_by=ResourceUsage.imported_at.desc(),
            partition_by=(ResourceUsage.resource_id,
                          ResourceUsage.usage_type_code)
        ).label('imported_rank')
    ).subquery(name='resource_usage')
    query = db.session.query(subquery).filter(
        subquery.c.imported_rank == 1,
        subquery.c.resource_name.like('%{}%'.format(str(param['resource_name']))),
        subquery.c.usage_type_code.like('%{}%'.format(str(param['usage_type_code'])))
    )
    return query


@api_bp.route('/resource_usages/<int:id>', methods=['GET'])
# @token_auth.login_required
def get_resource_usage_by_id(id):
    return jsonify(ResourceUsage.query.get_or_404(id).to_dict())


def get_resource_usage_by_resource_name(resource_name):
    resource_usage = ResourceUsage.query.filter_by(resource_name=resource_name).first()
    if resource_usage is None:
        abort(404)
    return jsonify(resource_usage.to_dict())


@api_bp.route('/resource_usages', methods=['GET'])
# @token_auth.login_required
def get_resource_usages():

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 1000, type=int), 100)

    # check null resource_id delete on production
    check_null_resource = ResourceUsage.query.filter_by(resource_id=None) 

    if(check_null_resource.count() > 0):
        for usage in check_null_resource:
            resource = Resource.query.filter_by(name=usage.resource_name).first()
            if resource is not None:
                usage.resource_id = resource.id
        db.session.commit()

    resource_id = request.args.get('resource_id', "", type=str)
    resource_name = request.args.get('resource_name', "", type=str)
    usage_type_code = request.args.get('type', "", type=str)
    latest_only = request.args.get('latest_only', 0, type=int)

    query = ResourceUsage.query.filter(
        ResourceUsage.resource_name.like('%{}%'.format(str(resource_name))),
        ResourceUsage.usage_type_code.like('%{}%'.format(str(usage_type_code)))
    )
    if resource_id != "":
        query.filter(ResourceUsage.resource_id == resource_id)

    data = {}
    # 2020-09-19T13:55:26Z
    query = query.order_by(ResourceUsage.imported_at.desc())

    if latest_only == 0:
        # IF NOT LATEST THEN FILTER BY IMPORT DATE
        date_string = request.args.get('from_date', "", type=str)
        if date_string != "":
            try:
                from_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    from_date = datetime.strptime(date_string, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "success": "error",
                        "error_message": "Invalid from_date format, accepting only '%Y-%m-%d %H:%M:%S' or '%Y-%m-%d'"
                    })
            query = query.filter(ResourceUsage.imported_at >= from_date)

        date_string = request.args.get('to_date', "", type=str)
        if date_string != "":
            try:
                to_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    to_date = datetime.strptime(date_string, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "success": "error",
                        "error_message": "Invalid to_date format, accepting  '%Y-%m-%d %H:%M:%S' or '%Y-%m-%d'"
                    })
            query = query.filter(cast(ResourceUsage.imported_at, Date) <= to_date)

    else:
        query = get_rt_resource_usage({
            "resource_name": resource_name,
            "usage_type_code": usage_type_code
        })
    # data = ResourceUsage.to_collection_dict(query,
    #                                        page, per_page, 'api.get_resource_usages')

    resource_usage_schema = ResourceUsageSchema(many=True)
    data = resource_usage_schema.dump(query)

    return jsonify({
        "_count": query.count(),
        "data": data  # ["items"]
    })


# http --auth nairobi:1234 POST https://oc-flask.herokuapp.com/api/tokens
# http POST http://localhost:5000/api/resource_usages name=VM1 parent_name=SERVER1 "imported_at=09/19/18 13:55:26"
# curl -i -H "Content-Type:application/plain" -X POST -d 'resource_name|usage_type_code|capacity|usage|available|uom_code|imported_at' http://localhost:5000/api/resource_usages
# curl -i -H "Content-Type:application/plain" -X POST -d 'VM2|MEM|100|10|80|MB|2020-09-19 13:55:26' http://localhost:5000/api/resource_usages
# -H "Authorization: Bearer lvVSR4oCIc3K+YDHFQuOuLG3eHa7BCPQ"
@api_bp.route('/resource_usages', methods=['POST'])
# @token_auth.login_required
def create_resource_usages():
    try:
        req = request.get_json(force=True)
        if req["data"] != "":
            data = req["data"]
        else:
            data = req
    except Exception:
        data = request.get_data().decode("utf-8")

    data = data.split("|")
    data = {
        "resource_name": data[0],
        "usage_type_code": data[1],
        "capacity": data[2],
        "usage": data[3],
        "available": data[4],
        "uom_code": data[5],
        "imported_at": data[6],
        "resource_id": (data[7] if data.count == 7 else '')
    }
    # data = request.get_json(force=True) or {}

    if data['resource_name'] == '' or data['usage_type_code'] == '':
        return bad_request('must include resource_name, usage_type_code and imported_at')

    if data['resource_id'] == '':
        data['resource_id'] = Resource.query.filter_by(name=data['resource_name']).first().id

    # resource_usage = ResourceUsage()
    # resource_usage.from_dict(data, new_data=True)
    # db.session.add(resource_usage)
    # db.session.commit()
    resource_usage_schema = ResourceUsageSchema(many=False)
    res = resource_usage_schema.load(data)
    db.session.add(res)
    db.session.commit()

    response = jsonify(resource_usage_schema.dump(res))
    response.headers['Location'] = url_for('api.get_resource_usage_by_id',
                                           id=res.id)
    resource_usage_schemas = ResourceUsageSchema(many=True)
    socketio.emit('listen-rt-usage',
                  resource_usage_schemas.dump(get_rt_resource_usage()),
                  broadcast=True)
    return response


@api_bp.route('/resource_usages/auth', methods=['POST'])
@token_auth.login_required
def create_resource_usages_auth():
    try:
        data = request.get_json(force=True)
    except Exception:
        data = request.get_data().decode("utf-8")

    data = data.split("|")
    data = {
        "resource_name": data[0],
        "usage_type_code": data[1],
        "capacity": data[2],
        "usage": data[3],
        "available": data[4],
        "uom_code": data[5],
        "imported_at": data[6]
    }
    # data = request.get_json(force=True) or {}

    if data['resource_name'] == '' or data['usage_type_code'] == '':
        return bad_request('must include resource_name, usage_type_code and imported_at')

    resource_usage = ResourceUsage()
    resource_usage.from_dict(data, new_data=True)
    db.session.add(resource_usage)
    db.session.commit()
    response = jsonify(resource_usage.to_dict())
    response.headers['Location'] = url_for('api.get_resource_usage_by_id',
                                           id=resource_usage.id)
    return response
