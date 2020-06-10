from app.api import api_bp
from flask import jsonify, request, url_for, abort
from app import db
from app.models import Resource, ResourceSchema
# from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request


# curl -i http://localhost:5000/api/users/1
@api_bp.route('/resource/<string:id>', methods=['GET'])
# @token_auth.login_required
def get_resource_by_id(id):
    if id is not None and id != '':
        return jsonify(Resource.query.get_or_404(id).to_dict())
    else:
        abort(404)


@api_bp.route('/filter_resources', methods=['GET'])
def get_resources_by_name():
    id = request.args.get('id', "", type=str)
    name = request.args.get('name', "", type=str)
    parent_name = request.args.get('parent_name', "", type=str)
    instance_type = request.args.get('instance_type', "", type=str)
    # first = request.args.get('first', 0, type=int)

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 1000, type=str), 100)

    query = Resource.query.filter(
        Resource.parent_name.like('%{}%'.format(str(parent_name))),
        Resource.name.like('%{}%'.format(str(name))),
        Resource.instance_type.like('%{}%'.format(str(instance_type)))
    )
    data = {}
    if id != "":
        query = query.filter(Resource.id == id)

    resource_schema = ResourceSchema(many=True)
    data = resource_schema.dump(query)

    # resource_usage_schema = ResourceUsageSchema(many=True)
    # test = resource_usage_schema.dump(query.filter_by(name='sda-app1').first().resource_usages)
    return jsonify({
        "_count": query.count(),
        # "data_items": data["items"]
        "data": data
    })


def get_resource_by_name(name):
    resource = Resource.query.filter_by(name=name).first()
    if resource is None:
        abort(404)
    return jsonify(resource.to_dict())


# curl -i http://localhost:5000/api/users/
@api_bp.route('/resources', methods=['GET'])
# @token_auth.login_required
def get_resources():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 1000, type=int), 100)
    query = Resource.query
    data = Resource.to_collection_dict(query, page, per_page,
                                       'api.get_resources')
    return jsonify({
        "_count": query.count(),
        "data": data["items"]
    })

# http POST http://localhost:5000/api/resources name=VM1 parent_name=SERVER1 "imported_at=09/19/18 13:55:26"
# curl -i -H "Content-Type:application/json" -X POST -d '{"name":"VM2", "parent_name":"SERVER1", "imported_at":"09/19/18 13:55:26"}' http://localhost:5000/api/resources
# curl -i -H "Content-Type:application/plain" -X POST -d '{"name":"VM2", "parent_name":"SERVER1", "imported_at":"09/19/18 13:55:26"}' http://localhost:5000/api/resources
# curl -i -H "Content-Type:application/plain" -X POST -d 'VMPLAIN1|SERVERPLAIN|VM|2020-09-19 13:55:26' http://localhost:5000/api/resources
# -H "Authorization: Bearer QFQWPX4GAtHp70VSxVeyfU6demPobwl3"
@api_bp.route('/resources', methods=['POST'])
# @token_auth.login_required
def create_resources():
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
        "name": data[0],
        "parent_name": data[1],
        "instance_type": data[2],
        "imported_at": data[3]
    }

    if 'name' not in data or 'parent_name' not in data or 'imported_at' not in data:
        return bad_request('must include name, parent_name, instance_type and imported_at')

    resource = Resource()
    resource.from_dict(data, new_data=True)
    db.session.add(resource)
    db.session.commit()
    response = {
        "isSucceed": True,
        "resource": resource.to_dict()
    }
    response = jsonify(response)
    response.headers['Location'] = url_for('api.get_resource_by_id',
                                        id=resource.id)
    return response

    # old_data = Resource.query.filter(Resource.name == data['name'],
    #                                  Resource.parent_name == data['parent_name']
    #                                  ).first()

    # if old_data is None:
    #     resource = Resource()
    #     resource.from_dict(data, new_data=True)
    #     db.session.add(resource)
    #     db.session.commit()
    #     response = {
    #         "isSucceed": True,
    #         "resource": resource.to_dict()
    #     }
    #     response = jsonify(response)
    #     response.headers['Location'] = url_for('api.get_resource_by_id',
    #                                            id=resource.id)
    # else:
    #     response = jsonify(old_data.to_dict())
    #     response.status_code = 201
    #     response.headers['Location'] = url_for('api.get_resource_by_id',
    #                                            id=old_data.id)


@api_bp.route('/resources/auth', methods=['POST'])
@token_auth.login_required
def create_resources_auth():
    try:
        data = request.get_json(force=True)
    except Exception:
        data = request.get_data().decode("utf-8")

    data = data.split("|")
    data = {
        "name": data[0],
        "parent_name": data[1],
        "instance_type": data[2],
        "imported_at": data[3]
    }
    # data = request.get_json(force=True) or {}

    if 'name' not in data or 'parent_name' not in data or 'imported_at' not in data:
        return bad_request('must include name, parent_name, instance_type and imported_at')

    old_data = Resource.query.filter(Resource.name == data['name'],
                                     Resource.parent_name == data['parent_name']
                                     ).first()

    if old_data is None:
        resource = Resource()
        resource.from_dict(data, new_data=True)
        db.session.add(resource)
        db.session.commit()
        response = jsonify(resource.to_dict())
        response.headers['Location'] = url_for('api.get_resource_by_id',
                                               id=resource.id)
    else:
        response = jsonify(old_data.to_dict())
        response.status_code = 201
        response.headers['Location'] = url_for('api.get_resource_by_id',
                                               id=old_data.id)
    return response
