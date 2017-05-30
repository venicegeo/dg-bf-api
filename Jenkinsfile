node ('python35') {

    stage('Setup') {
        git([
            url: 'https://github.com/venicegeo/bf-api.git',
            branch: 'master'
        ])
    }

    stage 'Test' {
        sh 'echo y | ./scripts/test.sh'
    }

    stage('Archive') {
        sh 'echo y | ./scripts/package.sh'
    }

    stage('Deploy') {
        cfPush()
        cfBgDeploy()
    }

    stage ('Cleanup') {
        deleteDir()
    }
}
