"""
    evaluate DST model
"""

import os
import json
import importlib

from tqdm import tqdm

from convlab2.dst import DST
from convlab2.dst.dstc9.utils import prepare_data, eval_states, dump_result


def evaluate(model_dir, subtask, test_data, gt):
    module = importlib.import_module(model_dir.replace('/', '.'))
    assert 'Model' in dir(module), 'please import your model as name `Model` in your subtask module root'
    model_cls = getattr(module, 'Model')
    assert issubclass(model_cls, DST), 'the model must implement DST interface'
    # load weights, set eval() on default
    model = model_cls()
    pred = {}
    bar = tqdm(total=sum(len(turns) for turns in test_data.values()), ncols=80, desc='evaluating')
    for dialog_id, turns in test_data.items():
        model.init_session()
        pred[dialog_id] = []
        for sys_utt, user_utt, gt_turn in turns:
            pred[dialog_id].append(model.update_turn(sys_utt, user_utt))
            bar.update()
    bar.close()

    result, errors = eval_states(gt, pred, subtask)
    print(json.dumps(result, indent=4))
    dump_result(model_dir, 'model-result.json', result, errors, pred)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('subtask', type=str, choices=['multiwoz', 'crosswoz'])
    parser.add_argument('split', type=str, choices=['train', 'val', 'test', 'human_val'])
    args = parser.parse_args()
    subtask = args.subtask
    test_data = prepare_data(subtask, args.split)
    gt = {
        dialog_id: [state for _, _, state in turns]
        for dialog_id, turns in test_data.items()
    }
    evaluate('example', subtask, test_data, gt)
