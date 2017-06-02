@Library('pipelib@master') _

node {

    stage('Setup') {
        git([
            url: 'https://github.com/venicegeo/dg-bf-api.git',
            branch: 'master'
        ])
    }

    stage('Test') {
        sh 'echo y | ./scripts/test.sh'
    }

    stage('Archive') {
        sh 'echo y | ./scripts/package.sh'
        // HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
        writeFile file: 'users.sh', text: '''#!/bin/bash -e

            cd ~/app

            source .profile.d/python.sh
            export MUTE_LOGS=1

            ./.cloudfoundry/python/bin/python -m beachfront.temporary_cli_for_user_admin "$@"
        '''
        sh 'zip beachfront.zip user-admin-cli.sh'
        // HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
    }

    stage('Create CloudFoundry manifest') {
        def props = readProperties(file: 'jenkins.properties')

        withEnv([
            "MANIFEST_OUTFILE=${props.get('cfManifest')}",
            "CATALOG_HOST=bf-ia-broker.${props.get('cfDomain')}",
            "PIAZZA_HOST=piazza.${props.get('cfDomain')}"
        ]) {
            withCredentials([[
                $class: 'UsernamePasswordBinding',
                credentialsId: 'beachfront-piazza-npe',
                variable: 'PIAZZA_AUTH'
            ]]) {
                sh 'echo y | ./scripts/create-cf-manifest.sh'
            }
        }
    }

    stage('Deploy') {
        try {
		cfPush()
        	cfBgDeploy()
	} finally {
		stage('Cleanup') {
			deleteDir()
		}
	}
    }
}
