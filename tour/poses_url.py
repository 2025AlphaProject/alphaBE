from django.conf import settings

s3_base_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}"

POSE_URL_MAP = {
    "A0101": [
        f"{s3_base_url}/image_8_1.png",
        f"{s3_base_url}/image_9_1.png",
        f"{s3_base_url}/image_10_1.png",
    ],
    "A0102": [
        f"{s3_base_url}/image_11.png",
        f"{s3_base_url}/image_12.png",
        f"{s3_base_url}/image_13.png",
    ],
    "A0201": [
        f"{s3_base_url}/image_14.png",
        f"{s3_base_url}/image_15.png",
        f"{s3_base_url}/image_16.png",
    ],
    "A0202": [
        f"{s3_base_url}/image_17.png",
        f"{s3_base_url}/image_18.png",
        f"{s3_base_url}/image_19.png",
    ],
    "A0203": [
        f"{s3_base_url}/image_20.png",
        f"{s3_base_url}/image_20.png",
        f"{s3_base_url}/image_21.png",
    ],
    "A0204": [
        f"{s3_base_url}/image_22.png",
        f"{s3_base_url}/image_23.png",
        f"{s3_base_url}/image_24.png",
    ],
    "A0205": [
        f"{s3_base_url}/image_25.png",
        f"{s3_base_url}/image_26.png",
        f"{s3_base_url}/image_27.png",
    ],
    "A0206": [
        f"{s3_base_url}/image_28.png",
        f"{s3_base_url}/image_29.png",
        f"{s3_base_url}/image_30.png",
    ],
    "A0207": [
        f"{s3_base_url}/image_31.png",
        f"{s3_base_url}/image_32.png",
        f"{s3_base_url}/image_33.png",
    ],
    "A0208": [
        f"{s3_base_url}/image_34.png",
        f"{s3_base_url}/image_35.png",
        f"{s3_base_url}/image_36.png",
    ],
    "A0301": [
        f"{s3_base_url}/image_37.png",
        f"{s3_base_url}/image_38.png",
        f"{s3_base_url}/image_39.png",
    ],
    "A0302": [
        f"{s3_base_url}/image_40.png",
        f"{s3_base_url}/image_41.png",
        f"{s3_base_url}/image_42.png",
    ],
    "A0303": [
        f"{s3_base_url}/image_43.png",
        f"{s3_base_url}/image_44.png",
        f"{s3_base_url}/image_45.png",
    ],
    "A0304": [
        f"{s3_base_url}/image_46.png",
        f"{s3_base_url}/image_47.png",
        f"{s3_base_url}/image_48.png",
    ],
    "A0305": [
        f"{s3_base_url}/image_81_1.png",
        f"{s3_base_url}/image_49.png",
        f"{s3_base_url}/image_50.png",
    ],
    "A0401": [
        f"{s3_base_url}/image_51.png",
        f"{s3_base_url}/image_52.png",
        f"{s3_base_url}/image_53.png",
    ],
    "A0502": [
        f"{s3_base_url}/image_54.png",
        f"{s3_base_url}/image_55.png",
        f"{s3_base_url}/image_56.png",
    ],
    "B0201": [
        f"{s3_base_url}/image_57.png",
        f"{s3_base_url}/image_58.png",
        f"{s3_base_url}/image_59.png",
    ],
    "C0112": [
        f"{s3_base_url}/image_60.png",
        f"{s3_base_url}/image_61_1.png",
        f"{s3_base_url}/image_62.png",
    ],
    "C0113": [
        f"{s3_base_url}/image_63.png",
        f"{s3_base_url}/image_64.png",
        f"{s3_base_url}/image_65.png",
    ],
    "C0114": [
        f"{s3_base_url}/image_66.png",
        f"{s3_base_url}/image_67.png",
        f"{s3_base_url}/image_68.png",
    ],
    "C0115": [
        f"{s3_base_url}/image_69.png",
        f"{s3_base_url}/image_70.png",
        f"{s3_base_url}/image_71.png",
    ],
    "C0116": [
        f"{s3_base_url}/image_72.png",
        f"{s3_base_url}/image_73.png",
        f"{s3_base_url}/image_74.png",
    ],
    "C0117": [
        f"{s3_base_url}/image_75.png",
        f"{s3_base_url}/image_76.png",
        f"{s3_base_url}/image_77.png",
    ],
    "None": [
        f"{s3_base_url}/image_78.png",
        f"{s3_base_url}/image_79.png",
        f"{s3_base_url}/image_80.png",
    ],
}
