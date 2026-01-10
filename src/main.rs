mod fetcher;

use serde::{Deserialize, Serialize};

use crate::fetcher::distfetch;

#[derive(Debug,Deserialize,Serialize)]
pub struct Package {
    version: String,
    build: String,
    depends: Option<Vec<String>>,
    distfiles: Option<Vec<Distfile>>,
}

#[derive(Debug,Deserialize,Serialize)]
pub struct Distfile {
    uri: String,
    blake2b: String,
    name: Option<String>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let package_name = std::env::args().nth(1).expect("expected package name");
    let package_definition = std::fs::read_to_string(format!("{package_name}.toml")).expect("couldn't read package definition");
    let package: Package = toml::from_str(&package_definition).expect("couldn't parse toml");
    if let Some(distfiles) = package.distfiles {
        for distfile in distfiles {
            distfetch(distfile, "/tmp/distfiles");
        }
    }
    Ok(())
}
