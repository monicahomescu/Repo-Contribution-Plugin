function validateInput(owner_repo, commit_count) {
    let errorMsg = "";

    if (!owner_repo.trim()) {
        errorMsg += "Please enter a valid owner/repo.\n";
    }

    if (isNaN(commit_count) || commit_count < 1 || commit_count > 10000) {
        errorMsg += "Please enter a number between 1 and 10000 for commits.";
    }

    return errorMsg.trim();
}

function updateNumbers(id, genderPercentage, coreCount, nonCoreCount) {
    document.getElementById(id + "-ratio").innerHTML = genderPercentage + "%";
    document.getElementById(id + "-core-number").innerHTML = coreCount;
    document.getElementById(id + "-non-core-number").innerHTML = nonCoreCount;
}

function updateMetrics(id, currentValue, averageValue) {
    let maxDiv = document.getElementById("max-" + id);
    let minDiv = document.getElementById("min-" + id);

    if (id === "core") {
        if (currentValue > averageValue) {
            maxDiv.innerHTML = "current - " + currentValue;
            minDiv.innerHTML = "average - " + averageValue;
        } else {
            maxDiv.innerHTML = "average - " + averageValue;
            minDiv.innerHTML = "current - " + currentValue;
        }
    }
    else {
        if (currentValue > averageValue) {
            maxDiv.innerHTML = currentValue + " - current";
            minDiv.innerHTML = averageValue + " - average";
        } else {
            maxDiv.innerHTML = averageValue + " - average";
            minDiv.innerHTML = currentValue + " - current";
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {
    let controller = new AbortController();
    window.addEventListener("unload", () => {
        controller.abort();
    });

    let ownerRepo = document.getElementById("owner-repo");
    chrome.tabs.query({currentWindow: true, active: true}, function(tabs) {
        let url = tabs[0].url;
        let match = url.match(/^https:\/\/github\.com\/([^\/]+)\/([^\/]+)(\/|$)/);

        if (match) {
            ownerRepo.value = `${match[1]}/${match[2]}`;
        }
    })

    let statusContainer = document.getElementById("status-container");
    statusContainer.addEventListener("click", async function (e) {
        if (e.target && e.target.id === "analyze-button") {
            let commitCount = document.getElementById("commit-count");

            let errorMsg = validateInput(ownerRepo.value, commitCount.value);
            if (!errorMsg) {
                statusContainer.innerHTML = '<div class="load-circle"></div>';

                try {
                    // let redirectUri = chrome.identity.getRedirectURL();
                    // let authUrl = `https://github.com/login/oauth/authorize?client_id=CLIENT_ID&redirect_uri=${encodeURIComponent(redirectUri)}&scope=repo`;

                    // chrome.identity.launchWebAuthFlow({ url: authUrl, interactive: true }, async (redirectUrl) => {
                    //     if (redirectUrl) {
                    //         let code = new URL(redirectUrl).searchParams.get("code"
                    //         );
                    //
                    //         if (code) {
                    let response = await fetch("http://localhost:8000/repo-stats", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            repo: ownerRepo.value,
                            count: commitCount.value,
                            //code: code
                        }),
                        signal: controller.signal
                    });
                    let data = await response.json();
                    let {count, date, female, male, nonbinary, unknown, core, noncore,
                        blauCore, avgBlauCore, blauNoncore, avgBlauNoncore, repos} = data;
                    let { female: femaleCore, male: maleCore, nonbinary: nonbinaryCore, unknown: unknownCore } = core;
                    let { female: femaleNoncore, male: maleNoncore, nonbinary: nonbinaryNoncore, unknown: unknownNoncore } = noncore;

                    let commitsText = document.getElementById("commits-text");
                    let today = new Date().toISOString().split("T")[0];
                    commitsText.innerHTML = "*Analyzed " + count + " commits (" + date + " <-> " + today + ")";
                    commitsText.style.visibility = "visible";

                    updateNumbers("female", female, femaleCore, femaleNoncore);
                    updateNumbers("male", male, maleCore, maleNoncore);
                    updateNumbers("nonbinary", nonbinary, nonbinaryCore, nonbinaryNoncore);
                    updateNumbers("unknown", unknown, unknownCore, unknownNoncore);

                    let averageText = document.getElementById("average-text");
                    if (repos === 0) {
                        document.getElementById("placeholder-core").innerHTML = "current - " + blauCore;
                        document.getElementById("placeholder-non-core").innerHTML = blauNoncore + " - current";
                        averageText.innerHTML = "*No other repos analyzed up to date for comparison"
                    }
                    else {
                        document.getElementById("placeholder-core")?.remove();
                        document.getElementById("placeholder-non-core")?.remove();
                        updateMetrics("core", blauCore, avgBlauCore);
                        updateMetrics("non-core", blauNoncore, avgBlauNoncore);
                        averageText.innerHTML = "*Average based on " + repos + " other repo(s) analyzed up to date"
                    }
                    averageText.style.visibility = "visible";

                    statusContainer.innerHTML = '<button id="analyze-button">Analyze</button>';
                    //     }
                    // }
                    // });
                } catch (error) {
                    if (error.name === "AbortError") {
                        console.log("Popup closed during request");
                    } else {
                        alert("Error: " + error.message);
                    }
                }
            } else {
                alert(errorMsg);
            }
        }
    });
})
