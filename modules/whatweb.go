//go:build whatweb
// +build whatweb

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "whatwebScanner"
	description    = "Identifies web technologies used by a target using WhatWeb"
	author         = "Your Name"
	category       = "Web"
	installCommand = "sudo apt install whatweb"
	dependencies   = []string{"whatweb"}
	parameters     = []map[string]interface{}{
		{"name": "target", "description": "Target URL to scan", "required": true, "default": ""},
		{"name": "follow_redirects", "description": "Follow HTTP redirects (true/false)", "required": false, "default": "true"},
		{"name": "verbose", "description": "Verbose output (true/false)", "required": false, "default": "false"},
		{"name": "user_agent", "description": "Custom User-Agent string", "required": false, "default": ""},
		{"name": "options", "description": "Additional WhatWeb options", "required": false, "default": ""},
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
		Target          string `json:"target"`
		FollowRedirects string `json:"follow_redirects"`
		Verbose         string `json:"verbose"`
		UserAgent       string `json:"user_agent"`
		Options         string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the WhatWeb command
	cmdArgs := []string{params.Target}

	// Add optional parameters based on user input
	if params.FollowRedirects == "false" {
		cmdArgs = append(cmdArgs, "--no-follow")
	}
	if params.Verbose == "true" {
		cmdArgs = append(cmdArgs, "--verbose")
	}
	if params.UserAgent != "" {
		cmdArgs = append(cmdArgs, "--user-agent", params.UserAgent)
	}

	// Include any additional WhatWeb options provided by the user
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	// Execute the WhatWeb command
	cmd := exec.Command("whatweb", cmdArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute whatweb: %s\"}\n", err)
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
