from typing import Dict


def run(visual_payload: Dict) -> Dict:
    # TODO: implement render stage and return artifact metadata.
    return {"stage": "render", "input": visual_payload, "artifact": None}
