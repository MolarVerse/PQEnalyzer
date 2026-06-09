from PQEnalyzer.plots.labels import unique_path_labels


def test_unique_path_labels_keep_unique_basenames():
    labels = unique_path_labels(["/tmp/a/md-01.en", "/tmp/b/md-02.en"])

    assert labels == ["md-01.en", "md-02.en"]


def test_unique_path_labels_use_parent_for_duplicate_basenames():
    labels = unique_path_labels(["/tmp/run-a/md.en", "/tmp/run-b/md.en"])

    assert labels == ["run-a/md.en", "run-b/md.en"]


def test_unique_path_labels_keep_unrelated_unique_basenames_short():
    labels = unique_path_labels([
        "/tmp/water/run-001/energy.out",
        "/tmp/methanol/run-001/energy.out",
        "/tmp/water/run-002/forces.out",
    ])

    assert labels == [
        "water/run-001/energy.out",
        "methanol/run-001/energy.out",
        "forces.out",
    ]


def test_unique_path_labels_number_identical_paths():
    labels = unique_path_labels(["/tmp/run/md.en", "/tmp/run/md.en"])

    assert labels == ["tmp/run/md.en", "tmp/run/md.en (2)"]
