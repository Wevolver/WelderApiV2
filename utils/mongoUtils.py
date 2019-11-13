def flattenOID(obj):
    _id = obj.get('_id', None)
    if not _id:
        return obj
    oid = _id.get('$oid', None)
    if not oid:
        return obj
    obj['_id'] = oid
    return obj