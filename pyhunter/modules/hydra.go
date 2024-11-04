//go:build hydra
// +build hydra

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "hydraBruteForce"
	description    = "Performs brute-force login attempts using Hydra with configurable options"
	author         = "Your Name"
	category       = "Web"
	installCommand = "sudo apt install hydra"
	dependencies   = []string{"hydra"}
	parameters     = []map[string]interface{}{
		{"name": "target", "description": "Target URL or IP address", "required": true, "default": ""},
		{"name": "service", "description": "Service to attack (e.g., http-get, ssh, ftp)", "required": true, "default": ""},
		{"name": "username", "description": "Username to use or path to wordlist for usernames", "required": false, "default": ""},
		{"name": "password", "description": "Password to use or path to wordlist for passwords", "required": false, "default": ""},
		{"name": "threads", "description": "Number of concurrent threads to use", "required": false, "default": "16"},
		{"name": "options", "description": "Additional Hydra options", "required": false, "default": ""},
	}
)

func main() {
	metadata := flag.Bool("metadata", false, "Output metadata as JSON")
	var paramsJSON string
	flag.StringVar(&paramsJSON, "params", "", "JSON string containing module parameters")
	flag.Parse()

	if *metadata {
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

	var params struct {
		Target   string `json:"target"`
		Service  string `json:"service"`
		Username string `json:"username"`
		Password string `json:"password"`
		Threads  string `json:"threads"`
		Options  string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the Hydra command
	cmdArgs := []string{"-l", params.Username, "-P", params.Password, "-t", params.Threads, params.Service, params.Target}

	// Add additional options if provided
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	// Execute the Hydra command
	cmd := exec.Command("hydra", cmdArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute hydra: %s\"}\n", err)
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
