import segmentation_models_pytorch as smp


def build_unet():
    """
    Returns the ResNet34 U-Net architecture used by the trained models.
    """

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=1,
        classes=1,
        activation=None,
    )

    return model
