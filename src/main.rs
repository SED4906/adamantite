use std::{fs, process::Command};
use which::which;
use toml::Table;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input = fs::read_to_string("Adamantite.toml")?;
    let table = (&input).parse::<Table>()?;
    let targets = table["build"]["targets"].as_array().expect("`build` section missing `targets` field");
    let deps = table["build"]["deps"].as_array().expect("`build` section missing `deps` field");
    for dep in deps {
        let dep_ = depend(dep.as_str().unwrap(), &table)?;
        for run in dep_["runs"].as_array().expect(format!("Dependency {dep} missing `runs` field").as_str()) {
            let run_path = which::<String>(run.as_str().unwrap().into()).expect(format!("could not find {run} in PATH").as_str());
            println!("Dependency {dep}: Found {} in PATH",run_path.display())
        }
    }
    for tgt in targets {
        let tgt_ = target(tgt.as_str().unwrap(), &table)?;
        for cmd in tgt_["cmds"].as_array().expect(format!("Target {tgt} missing `cmds` field").as_str()) {
            println!("Target {tgt}: Running {cmd}");
            let status = if cfg!(target_os = "windows") {
                Command::new("cmd")
                    .args(["/C", cmd.as_str().unwrap()])
                    .status()
                    .expect("failed to execute process")
            } else {
                Command::new("sh")
                    .arg("-c")
                    .arg(cmd.as_str().unwrap())
                    .status()
                    .expect("failed to execute process")
            };
            if !status.success() {
                panic!("error: {cmd} returned status code {status}");
            }
        }
    }
    Ok(())
}

pub fn depend<'a>(name: &str, table: &'a Table) -> Result<&'a Table, Box<dyn std::error::Error>> {
    let subtable = table["depend"][name].as_table().expect(format!("Dependency {name} is missing or invalid").as_str());
    Ok(subtable)
}

pub fn target<'a>(name: &str, table: &'a Table) -> Result<&'a Table, Box<dyn std::error::Error>> {
    let subtable = table["target"][name].as_table().expect(format!("Target {name} is missing or invalid").as_str());
    Ok(subtable)
}