from conans import ConanFile, CMake, tools
import os

class ZlibConan(ConanFile):
    name = "zlib"
    author = "Ralph-Gordon Paul (gordon@rgpaul.com)"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "android_ndk": "ANY", "android_stl_type":["c++_static", "c++_shared"]}
    default_options = "shared=False", "android_ndk=None", "android_stl_type=c++_static"
    description = "Compressing File-I/O Library"
    url = "https://github.com/RGPaul/conan-zlib-scripts"
    license = "Zlib"
    exports_sources = "cmake-modules/*"

    # download zlib sources
    def source(self):
        url = "https://zlib.net/zlib%s.zip" % self.version.replace(".","")
        tools.get(url)

    # compile using cmake
    def build(self):
        cmake = CMake(self)
        zlib_folder = "%s/zlib-%s" % (self.source_folder, self.version)
        cmake.verbose = True

        if self.settings.os == "Android":
            self.applyCmakeSettingsForAndroid(cmake)

        if self.settings.os == "iOS":
            self.applyCmakeSettingsForiOS(cmake)

        if self.settings.os == "Macos":
            self.applyCmakeSettingsFormacOS(cmake)

        cmake.configure(source_folder=zlib_folder)
        cmake.build()
        cmake.install()

        lib_dir = os.path.join(self.package_folder,"lib")

        if self.settings.os == "Android":
            # delete shared artifacts for static builds and the static library for shared builds
            if self.options.shared:
                os.remove('%s/lib/libz.a' % self.package_folder)
            else:
                os.remove('%s/lib/libz.so' % self.package_folder)

        if self.settings.os == "iOS":
            # delete shared artifacts for static builds and the static library for shared builds
            if self.options.shared:
                # delete static library
                os.remove('%s/lib/libz.a' % self.package_folder)
            else:
                # delete dynamic library
                [os.remove(os.path.join(lib_dir,f)) for f in os.listdir(lib_dir) if f.endswith(".dylib")]
                
        if self.settings.os == "Linux":
            # delete shared artifacts for static builds and the static library for shared builds
            if self.options.shared:
                os.remove('%s/lib/libz.a' % self.package_folder)
            else:
                for f in os.listdir(lib_dir):
                    if f.startswith("libz.so"):       
                        os.remove(os.path.join(lib_dir,f))

        if self.settings.os == "Macos":
            # delete shared artifacts for static builds and the static library for shared builds
            if self.options.shared:
                os.remove('%s/lib/libz.a' % self.package_folder)
            else:
                [os.remove(os.path.join(lib_dir,f)) for f in os.listdir(lib_dir) if f.endswith(".dylib")]

        if self.settings.os == "Windows":
            libname = "zlib"
            static_libname = "zlibstatic"
            if self.settings.build_type == "Debug":
                libname = "zlibd"
                static_libname = "zlibstaticd"

            # delete shared artifacts for static builds and the static library for shared builds
            if self.options.shared:
                os.remove('%s/lib/%s.lib' % (self.package_folder, static_libname))
            else:
                os.remove('%s/bin/%s.dll' % (self.package_folder, libname))
                os.remove('%s/lib/%s.lib' % (self.package_folder, libname))
                os.rename('%s/lib/%s.lib' % (self.package_folder, static_libname), '%s/lib/%s.lib' % (self.package_folder, libname))

    def applyCmakeSettingsForAndroid(self, cmake):
        android_toolchain = os.environ["ANDROID_NDK_PATH"] + "/build/cmake/android.toolchain.cmake"
        cmake.definitions["CMAKE_SYSTEM_NAME"] = "Android"
        cmake.definitions["CMAKE_TOOLCHAIN_FILE"] = android_toolchain
        cmake.definitions["ANDROID_NDK"] = os.environ["ANDROID_NDK_PATH"]
        cmake.definitions["ANDROID_ABI"] = tools.to_android_abi(self.settings.arch)
        cmake.definitions["ANDROID_STL"] = self.options.android_stl_type
        cmake.definitions["ANDROID_NATIVE_API_LEVEL"] = self.settings.os.api_level
        cmake.definitions["ANDROID_TOOLCHAIN"] = "clang"

    def applyCmakeSettingsForiOS(self, cmake):
        ios_toolchain = "cmake-modules/Toolchains/ios.toolchain.cmake"
        cmake.definitions["CMAKE_TOOLCHAIN_FILE"] = ios_toolchain
        cmake.definitions["DEPLOYMENT_TARGET"] = "10.0"

        if self.settings.arch == "x86":
            cmake.definitions["PLATFORM"] = "SIMULATOR"
        elif self.settings.arch == "x86_64":
            cmake.definitions["PLATFORM"] = "SIMULATOR64"
        else:
            cmake.definitions["PLATFORM"] = "OS"

        # define all architectures for ios fat library
        if "arm" in self.settings.arch:
            cmake.definitions["ARCHS"] = "armv7;armv7s;arm64;arm64e"
        else:
            cmake.definitions["ARCHS"] = tools.to_apple_arch(self.settings.arch)

    def applyCmakeSettingsFormacOS(self, cmake):
        cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = tools.to_apple_arch(self.settings.arch)

    def package(self):
        self.copy("*", dst="include", src='include')
        self.copy("*.lib", dst="lib", src='lib', keep_path=False)
        self.copy("*.dll", dst="bin", src='bin', keep_path=False)
        self.copy("*.so", dst="lib", src='lib', keep_path=False)
        self.copy("*.dylib", dst="lib", src='lib', keep_path=False)
        self.copy("*.a", dst="lib", src='lib', keep_path=False)
        
    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs = ['include']

    def package_id(self):
        if "arm" in self.settings.arch and self.settings.os == "iOS":
            self.info.settings.arch = "AnyARM"

    def config_options(self):
        # remove android specific option for all other platforms
        if self.settings.os != "Android":
            del self.options.android_ndk
            del self.options.android_stl_type
