from ripe.atlas.cousteau import AtlasStopRequest,AtlasResultsRequest

def stop_measurement(msm):
    ATLAS_STOP_API_KEY = "42f5aee4-e4d0-4570-a5cf-b31384860e44"

    atlas_request = AtlasStopRequest(msm_id=msm, key=ATLAS_STOP_API_KEY)

    (is_success, response) = atlas_request.create()
    return response

def retreive_msm(msm):
    kwargs = {
        "msm_id": msm
    }

    is_success, results = AtlasResultsRequest(**kwargs).create()
    return results

with open('producer_trace.txt','r') as f:
    lines = f.readlines()
    lines = [line.strip().split('-')[-1] for line in lines]
    for line in lines:
        try:
            stop_measurement(int(line))
        except Exception as e:
            print(line)
            print(type(line))
            print(retreive_msm(line))
            break
            

