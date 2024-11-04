//go:build feroxbuster
// +build feroxbuster

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "feroxbusterScan"
	description    = "Performs a directory brute force scan on the target URL"
	author         = "Your Name"
	category       = "Web Application"
	installCommand = "cargo install feroxbuster" // Specify the install command for dependencies
	dependencies   = []string{"feroxbuster"}     // Specify required dependencies
	parameters     = []map[string]interface{}{
		{"name": "url", "description": "Target URL", "required": true, "default": ""},
		{"name": "wordlist", "description": "Path to wordlist", "required": false, "default": "common.txt"},
		{"name": "threads", "description": "Number of threads to use", "required": false, "default": "10"},
	}
)

func main() {
	metadata := flag.Bool("metadata", false, "Output metadata as JSON")
	var paramsJSON string
	flag.StringVar(&paramsJSON, "params", "", "JSON string containing module parameters")
	flag.Parse()

	if *metadata {
		// Output the metadata as JSON and exit
		meta := map[string]interface{}{
			"name":            name,
			"description":     description,
			"author":          author,
			"category":        category,
			"parameters":      parameters,
			"dependencies":    dependencies,
			"install_command": installCommand,
		}
		metaJSON, _ := json.Marshal(meta)
		fmt.Println(string(metaJSON))
		return
	}

	// Normal operation mode for executing the module logic
	var params struct {
		URL      string `json:"url"`
		Wordlist string `json:"wordlist"`
		Threads  string `json:"threads"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	cmd := exec.Command("feroxbuster", "-u", params.URL, "-w", params.Wordlist, "--threads", params.Threads)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute feroxbuster: %s\"}\n", err)
		os.Exit(1)
	}

	result := struct {
		Output string `json:"output"`
	}{
		Output: string(output),
	}
	resultJSON, _ := json.Marshal(result)
	fmt.Println(string(resultJSON))
}
