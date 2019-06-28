from conans import ConanFile, CMake, tools
import os

class ZlibConan(ConanFile):
    name = "zlib"
    version = "1.2.11"
    author = "Ralph-Gordon Paul (gordon@rgpaul.com)"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "android_ndk": "ANY", "android_stl_type":["c++_static", "c++_shared"]}
    default_options = "shared=False", "android_ndk=None", "android_stl_type=c++_static"
    description = "Compressing File-I/O Library"
    url = "https://github.com/Manromen/conan-zlib-scripts"
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
            cmake.definitions["CMAKE_SYSTEM_VERSION"] = self.settings.os.api_level
            cmake.definitions["CMAKE_ANDROID_NDK"] = os.environ["ANDROID_NDK_PATH"]
            cmake.definitions["CMAKE_ANDROID_NDK_TOOLCHAIN_VERSION"] = self.settings.compiler
            cmake.definitions["CMAKE_ANDROID_STL_TYPE"] = self.options.android_stl_type

        if self.settings.os == "iOS":
            ios_toolchain = "cmake-modules/Toolchains/ios.toolchain.cmake"
            cmake.definitions["CMAKE_TOOLCHAIN_FILE"] = ios_toolchain
            if self.settings.arch == "x86" or self.settings.arch == "x86_64":
                cmake.definitions["IOS_PLATFORM"] = "SIMULATOR"
            else:
                cmake.definitions["IOS_PLATFORM"] = "OS"

            # define all architectures for ios fat library
            if "arm" in self.settings.arch:
                self.variants = ["armv7", "armv7s", "armv8"]
            else:
                self.variants = []

            # apply build config for all defined architectures
            if len(self.variants) > 0:
                archs = ""
                for i in range(0, len(self.variants)):
                    if i == 0:
                        archs = tools.to_apple_arch(self.variants[i])
                    else:
                        archs += ";" + tools.to_apple_arch(self.variants[i])
                cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = archs
            else:
                cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = tools.to_apple_arch(self.settings.arch)

        if self.settings.os == "Macos":
            cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = tools.to_apple_arch(self.settings.arch)

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
                static_lib = os.path.join(lib_dir,"libz.a")
                self.run("xcrun ranlib %s" % static_lib)
                
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
