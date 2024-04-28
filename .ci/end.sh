ccache -s -v

if [ ! -z "${ANDROID_KEYSTORE_B64}" ]; then
    chmod +x ${GITHUB_WORKSPACE}/src/android/app/ks.jks
    rm "${GITHUB_WORKSPACE}/src/android/app/ks.jks"
fi
