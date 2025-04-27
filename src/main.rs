use std::{fs, process::Command};
use toml::Table;
use which::which;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input = fs::read_to_string("Adamantite.toml")?;
    let table = (&input).parse::<Table>()?;
    let targets = table["build"]["targets"]
        .as_array()
        .expect("`build` section missing `targets` field");
    let default_target = table["build"]["default"]
        .as_str()
        .expect("`build` section missing `default` field");
    let runs = table["runs"]
        .as_table()
        .expect("Missing `runs` section")
        .into_iter();
    for run in runs {
        let run_path = which::<String>(
            run.1
                .as_str()
                .expect(format!("Run {}: expected a string", run.0).as_str())
                .into(),
        )
        .expect(format!("could not find {} in PATH", run.1).as_str());
        println!("Run {}: Found {} in PATH", run.0, run_path.display());
    }
    let start_target = if targets.contains(&toml::Value::String(std::env::args().last().unwrap())) {
        std::env::args().last().unwrap().to_owned()
    } else {
        default_target.to_owned()
    };
    target(&start_target, &table)?;
    Ok(())
}

fn target(name: &String, table: &Table) -> Result<(), Box<dyn std::error::Error>> {
    let subtable = table["target"][name]
        .as_table()
        .expect(format!("Target {name} is missing or invalid").as_str());
    for cmd in subtable["cmds"]
        .as_array()
        .expect(format!("Target {name} missing `cmds` field.").as_str())
    {
        println!("Target {name}: Running {cmd}");
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

    Ok(())
}
