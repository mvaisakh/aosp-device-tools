#!/usr/bin/env bash

# Copyright 2014 The Android Open Source Project
# Copyright 2024 StatiXOS
#
# SPDX-License-Identifier: Apache-2.0
# 

if test "$1" = "" -o "$2" = ""
then
  echo "Need a manufacturer name and a device name"
  exit 1
fi

mkdir -p device/$1/$2
mkdir -p device/$1/$2-kernel
mkdir -p vendor/$1/$2

cat > device/$1/$2/AndroidProducts.mk << EOF
#
# Copyright 2014 The Android Open-Source Project
# Copyright 2024 StatiXOS
#
# SPDX-License-Identifier: Apache-2.0
# 

PRODUCT_MAKEFILES := \$(LOCAL_DIR)/statix_$2.mk

COMMON_LUNCH_CHOICES := statix_$2-userdebug
EOF

cat > device/$1/$2/statix_$2.mk << EOF
#
# Copyright 2014 The Android Open-Source Project
# Copyright 2024 StatiXOS
#
# SPDX-License-Identifier: Apache-2.0
# 
\$(call inherit-product, \$(SRC_TARGET_DIR)/product/full_base.mk)
\$(call inherit-product, device/$1/$2/device.mk)

PRODUCT_NAME := statix_$2
PRODUCT_DEVICE := $2
PRODUCT_BRAND := $1
PRODUCT_MODEL := $2
PRODUCT_MANUFACTURER := $1
EOF

cat > device/$1/$2/device.mk << EOF
#
# Copyright 2014 The Android Open-Source Project
# Copyright 2024 StatiXOS
#
# SPDX-License-Identifier: Apache-2.0
# 

ifeq (\$(TARGET_PREBUILT_KERNEL),)
LOCAL_KERNEL := device/$1/$2-kernel/kernel
else
LOCAL_KERNEL := \$(TARGET_PREBUILT_KERNEL)
endif

PRODUCT_COPY_FILES := \\
	\$(LOCAL_KERNEL):kernel

\$(call inherit-product-if-exists, vendor/$1/$2/device-vendor.mk)
EOF

cat > device/$1/$2/BoardConfig.mk << EOF
#
# Copyright 2014 The Android Open-Source Project
# Copyright 2024 StatiXOS
#
# SPDX-License-Identifier: Apache-2.0
# 

# Use the non-open-source parts, if they're present
-include vendor/$1/$2/BoardConfigVendor.mk

TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-2a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
EOF

touch device/$1/$2-kernel/kernel
touch device/$1/$2-kernel/MODULE_LICENSE_GPL

cat > vendor/$1/$2/device-vendor.mk << EOF
#
# Copyright 2014 The Android Open-Source Project
# Copyright 2024 StatiXOS
#
# SPDX-License-Identifier: Apache-2.0
# 
EOF

cat > vendor/$1/$2/BoardConfigVendor.mk << EOF
#
# Copyright 2014 The Android Open-Source Project
# Copyright 2024 StatiXOS
#
# SPDX-License-Identifier: Apache-2.0
# 
EOF

