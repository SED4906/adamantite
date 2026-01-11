use reqwest::Url;

use crate::Package;

pub fn build_no_sandbox(package: Package, package_name: &str) {
    if std::fs::exists("/tmp/build").expect("couldn't check for old build directory") {
        std::fs::remove_dir_all("/tmp/build").expect("couldn't remove build directory");
    }
    std::fs::create_dir_all("/tmp/build").expect("couldn't create build directory");
    std::fs::create_dir("/tmp/build/work").expect("couldn't create work directory");
    std::fs::create_dir("/tmp/build/out").expect("couldn't create out directory");
    for distfile in &package.distfiles.unwrap_or_default() {
        let name = distfile.name.clone().unwrap_or_else(|| {
            Url::parse(&distfile.uri)
                .expect("couldn't parse uri")
                .path_segments()
                .and_then(|mut segments| segments.next_back())
                .and_then(|name| if name.is_empty() { None } else { Some(name) })
                .expect("don't know what name to use")
                .to_string()
        });
        std::fs::copy(
            format!("/tmp/distfiles/{name}"),
            format!("/tmp/build/work/{name}"),
        )
        .expect("failed to copy distfile");
    }
    std::fs::write("/tmp/build/build", package.build).expect("couldn't write build script");
    let build_status = std::process::Command::new("bash")
        .args(vec!["-e", "/tmp/build/build"])
        .current_dir("/tmp/build/work")
        .env("PACKAGE_OUT", "/tmp/build/out")
        .status()
        .expect("failed to run bash");
    if !build_status.success() {
        panic!("build failed");
    }
    std::process::Command::new("tar")
        .args(vec![
            "cf",
            &format!("{package_name}_{}.tar", package.version),
            "-C",
            "/tmp/build/out",
            ".",
        ])
        .status()
        .expect("failed to run tar");
}
