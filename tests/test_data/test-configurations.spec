%define name test-configurations
%define version 0.1
%define release 1

Summary: Test package for ks extraction
Name: %{name}
Version: %{version}
Release: %{release}
Source0: test-image.ks
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Vendor <vendor@example.com>

%description
This is a test package for the download_kickstarts unit tests.

%prep

%build

%install
rm -rf %{buildroot}
install -d  %{buildroot}/usr/share/configurations
install %{SOURCE0} %{buildroot}/usr/share/configurations


%files
%defattr(-,root,root)
/usr/share/configurations
