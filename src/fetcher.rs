use reqwest::Url;

use blake2::{
    Blake2bVar,
    digest::{Update, VariableOutput},
};

use crate::Distfile;

pub fn distfetch(distfile: Distfile, distdir: &str) {
    print!("distfile {}", distfile.uri);
    let name = distfile.name.clone().unwrap_or_else(|| {
        Url::parse(&distfile.uri).expect("couldn't parse uri")
        .path_segments()
        .and_then(|mut segments| segments.next_back())
        .and_then(|name| if name.is_empty() { None } else { Some(name) })
        .expect("don't know what name to use")
        .to_string()
    });
    print!(" -> {name}");
    if let Ok(buf) = std::fs::read(format!("{distdir}/{name}")) {
        print!(" (already downloaded)");
        verify(distfile, buf);
    } else {
        print!(" (fetch)");
        fetch_and_verify(distfile, distdir);
    }
    println!(" OK");
}

fn verify(distfile: Distfile, buf: Vec<u8>) {
    let b2bytes = distfile.blake2b.len() / 2;
    let mut b2hasher = Blake2bVar::new(b2bytes).expect("couldn't create hasher");
    b2hasher.update(&buf);
    let mut hash_buf = vec![0u8; b2bytes];
    b2hasher
    .finalize_variable(&mut hash_buf)
    .expect("couldn't hash");
    if hex::decode(distfile.blake2b.clone()).expect("couldn't decode blake2b as hex") != hash_buf {
        panic!(
            "!!! failed blake2b checksum (expected {}, got {}) !!!",
               distfile.blake2b,
               hex::encode(hash_buf)
        );
    }
}

fn fetch_and_verify(distfile: Distfile, distdir: &str) {
    let response = reqwest::blocking::get(&distfile.uri).expect("couldn't get distfile");
    // Don't parse response.url() for the name here, it might've been changed.
    let name = distfile.name.clone().unwrap_or_else(|| {
        Url::parse(&distfile.uri).expect("couldn't parse uri")
        .path_segments()
        .and_then(|mut segments| segments.next_back())
        .and_then(|name| if name.is_empty() { None } else { Some(name) })
        .expect("don't know what name to use")
        .to_string()
    });
    let buf = response.bytes().expect("couldn't get bytes");
    verify(distfile, buf.to_vec());
    std::fs::write(format!("{distdir}/{name}"), &buf).expect("failed to create file");
}
