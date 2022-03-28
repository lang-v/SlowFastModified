#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.

"""Wrapper to train and test a video classification model."""
from slowfast.config.defaults import assert_and_infer_cfg
from slowfast.utils.misc import launch_job
from slowfast.utils.parser import load_config, parse_args

from tools.demo_net import demo
from tools.test_net import test
from tools.train_net import train
from tools.visualization import visualize


def main(source_path=None, task_queue=None):
    """
    Main function to spawn the train and test process.
    @param callback 当计算完成后通过此方法将视频帧返回
    """
    args = parse_args()
    cfg = load_config(args)
    cfg = assert_and_infer_cfg(cfg)

    # 动态设置视频输入源
    if source_path is not None:
        cfg.WEBCAM = -1
        cfg.DEMO.INPUT_VIDEO = source_path

    if source_path == '0':
        cfg.WEBCAM = 1
        print("run_net:on webcam {}".format(source_path))

    # Perform training.
    if cfg.TRAIN.ENABLE:
        launch_job(cfg=cfg, init_method=args.init_method, func=train)

    # Perform multi-clip testing.
    if cfg.TEST.ENABLE:
        launch_job(cfg=cfg, init_method=args.init_method, func=test)

    # Perform model visualization.
    if cfg.TENSORBOARD.ENABLE and (
        cfg.TENSORBOARD.MODEL_VIS.ENABLE
        or cfg.TENSORBOARD.WRONG_PRED_VIS.ENABLE
    ):
        launch_job(cfg=cfg, init_method=args.init_method, func=visualize)

    # Run demo.
    if cfg.DEMO.ENABLE:
        demo(cfg, task_queue)


if __name__ == "__main__":
    # torch.cuda.set_per_process_memory_fraction(0.8)
    main()
