from setuptools import find_packages, setup


setup(
    name="syncify",
    version="1.0.0",
    description="Spotify track and playlist metadata library",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.7.0",
    packages=find_packages(include=["syncify*"]),
    include_package_data=True,
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.12.0",
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
    ],
    extras_require={
        "dev": ["mutagen>=1.47.0"],
    },
    entry_points={
        "console_scripts": [
            "syncify=syncify.__main__:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords=["spotify", "playlist", "track", "metadata"],
    author="adelelawady",
)

