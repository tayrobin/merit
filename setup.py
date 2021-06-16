from distutils.core import setup
setup(
  name = 'merit',
  packages = ['merit'],
  version = '0.7',
  license='MIT',
  description = 'A Python SDK for the Merit API.',
  author = 'Taylor Robinson',
  author_email = 'taylor.howard.robinson@gmail.com',
  url = 'https://github.com/tayrobin/merit',
  download_url = 'https://github.com/tayrobin/merit/archive/refs/tags/0.7.tar.gz',
  keywords = ['Merit', 'API', 'SDK', 'Digital Credentials'],
  install_requires=[
          'requests',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)
